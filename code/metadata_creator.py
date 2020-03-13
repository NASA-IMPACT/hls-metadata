import os
import datetime
import re
import json
import update_credentials
import boto3
import logging

from dicttoxml import dicttoxml
from pyhdf.SD import SD, SDC
from pyproj import Proj, transform
from botocore.exceptions import ClientError


class Metadata:
    def __init__(self, data_file, obj):
        # initialize the granule level metadata file
        self.root = {
            "GranuleUR": "",
            "InsertTime": "",
            "Collection": {},
            "DataGranule": {},
            "Temporal": {},
            "Spatial": {},
            "Platforms": {},
            "OnlineAccessURLs": {"OnlineAccessURL": {}},
            "OnlineResources": {"OnlineResource": {}},
            "AssociatedBrowseImageURLs": {"ProviderBrowseURL": {}},
            "AdditionalAttributes": {},
            "Orderable": "",
            "DataFormat": "",
            "Visible": "",
        }
        self.data_file = data_file
        self.object = obj
        self.bucket = "hls-global"

    def extract_and_store(self):
        """
        Public: Main method to run. Extract and store information in echo10
                format.
        Examples
          m = Metadata('<file path>')
          m.extract_and_store_metadata()
          # => `<output cmr.xml s3 path>`

        Returns output in cmr.xml file that is
        loaded to hls-global/[S/L]30/metadata.
        """
        self.extract_attributes()
        self.template_handler()
        self.attribute_handler()
        # self.online_resource() - will be handled by LPDAAC
        self.data_granule_handler()
        self.time_handler()
        self.location_handler()
        result = self.post_processing()
        return result

    def extract_attributes(self):
        # extract the attributes from the data file
        granule = SD(self.data_file, SDC.READ)
        self.attributes = granule.attributes()
        granule.end()

    def template_handler(self):
        """
        there are several fields that will consistent across all granules
        in addition - there are a number of additional attribute fields that
        need to be filled for S30 and L30. The L30.json and S30.json sets the
        constant values and establishes the required list of additional
        attributes for each granule.
        """
        self.product = self.data_file.split(".")[1]
        with open("../util/" + self.product + ".json", "r") as template_file:
            template = json.load(template_file)
        template = template[self.product]
        spacecraft_name = self.attributes.get("SPACECRAFT_NAME")
        platform = "LANDSAT-8" if spacecraft_name is None else spacecraft_name
        self.root["Collection"]["DataSetId"] = template["DataSetId"]
        self.data_format = self.data_file.split(".")[-1]
        self.root = {
            **self.root,
            "Platforms": template[platform],
            "AdditionalAttributes": template["AdditionalAttributes"],
            "GranuleUR": self.data_file.replace("." + self.data_format, ""),
            "Orderable": template["Orderable"],
            "Visible": template["Visible"],
            "DataFormat": self.data_format,
        }

    def attribute_handler(self):
        """
        Loops through the attributes in the template file.
        Some of the additional attribute metadata names are inconsistent
        with the names in the hdf file. The attribute_mapping json file
        provides this mapping so that the appropriate value can be added
        for each of the additional attribute fields.
        """
        with open(
            "../util/" + self.product + "_attribute_mapping.json", "r"
        ) as attribute_file:
            attribute_mapping = json.load(attribute_file)
        for attribute in self.root["AdditionalAttributes"][
            "AdditionalAttribute"
        ]:
            attribute_name = attribute_mapping[attribute["Name"]]
            attribute["Value"] = self.attributes.get(
                attribute_name, "Not Available"
            )

    def online_resource(self):
        """
        This establishes the OnlineAccessURL which is the location where
        the data file can be downloaded (Need to address this when switching
        to COG - is this one link with a zip extension or do we have an
        AccessURL for each data file?). OnlineResourceURLs are also built
        here and those point to the browse and metadata files.
        """
        path = "s3://" + "/".join([self.bucket, self.product, "data"])
        self.root["OnlineAccessURLs"]["OnlineAccessURL"] = {
            "URL": "/".join([path, self.data_file]),
            "URLDescription": (
                "This file may be downloaded directly from this link"
            ),
            "MimeType": "application/x-" + self.data_format,
        }
        self.root["OnlineResources"]["OnlineResource"] = {
            "URL": "/".join(
                [
                    path.replace("data", "metadata"),
                    self.data_file.replace(self.data_format, "cmr.xml"),
                ]
            ),
            "Type": "EXTENDED METADATA",
            "MimeType": "text/xml",
        }
        self.root["AssociatedBrowseImageURLs"]["ProviderBrowseURL"] = {
            "URL": "/".join(
                [
                    path.replace("data", "thumbnail"),
                    self.data_file.replace(self.data_format, "jpeg"),
                ]
            ),
            "Description": (
                "This Browse file may be downloaded directly from this link"
            ),
        }

    def data_granule_handler(self):
        """
        Here we fill the required values for the DataGranule dictionary
        using the data file name, the data file attributes, and the
        S3 object summary. The code also normalizes processing time
        to match the format of the times written in the time_handler
        """
        try:
            production_datetime = datetime.datetime.strptime(
                self.attributes["HLS_PROCESSING_TIME"], "%Y-%m-%dT%H:%M:%SZ"
            )
            production_date = production_datetime.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
        except Exception:
            production_date = self.attributes["HLS_PROCESSING_TIME"]
        version = self.data_file[-7:].replace("." + self.data_format, "")
        extension = "." + ".".join(["v" + version, self.data_format])
        data_granule = {
            "SizeMBDataGranule": self.object.size,
            "ProducerGranuleId": self.data_file.replace(extension, ""),
            "DayNightFlag": "DAY",
            "ProductionDateTime": production_date,
            "LocalVersionId": self.data_file[-7:].replace(
                "." + self.data_format, ""
            ),
        }
        self.root["DataGranule"] = data_granule

    def time_handler(self):
        """
        This method handles the additional temporal fields in the metadata
        file. The time format is specified for each of the times provided.
        The granule file will handle if there is a SingleDateTime or a
        RangeDateTime based on the number of values in the SENSING_TIME
        attribute within the data file (Note: We need to confirm with Jeff
        and Junchang that these are the appropriate fields.
        """
        time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        self.root = {
            **self.root,
            "InsertTime": datetime.datetime.utcnow().strftime(time_format),
        }

        sensing_time = self.attributes["SENSING_TIME"].split(";")
        temporal = self.root["Temporal"]
        if len(sensing_time) == 1:
            time = datetime.datetime.strptime(sensing_time[0][:-2],time_format[:-1])
            temporal["SingleDateTime"] = time.strftime(time_format)
        else:
            time1 = datetime.datetime.strptime(sensing_time[0][:-2],time_format[:-1])
            time2 = datetime.datetime.strptime(sensing_time[-1][:-2].replace(' ',''),time_format[:-1])
            temporal["RangeDateTime"] = {
                "BeginningDateTime": time1.strftime(time_format),
                "EndingDateTime": time2.strftime(time_format),
            }
        self.root["Temporal"] = temporal

    def lat_lon_4326(self, bound):
        """
        Public: Change coordinates into proper projection (EPSG:4326)

        Examples

          m = Metadata('<file path>')
          m.lat_lon_4326([])
          # => []

        Returns the boundingbox in EPSG:4326 format
        """
        hdf_proj = Proj(init="EPSG:3857")
        reproj_proj = Proj(init="EPSG:4326")
        top_left_lon, top_left_lat = transform(
            hdf_proj, reproj_proj, bound[0], bound[1]
        )
        bottom_right_lon, bottom_right_lat = transform(
            hdf_proj, reproj_proj, bound[2], bound[3]
        )
        return [top_left_lon, top_left_lat, bottom_right_lon, bottom_right_lat]

    def location_handler(self):
        """
        The location handler establishes the geometry fields in the
        metadata file - specifically the bounding box information.
        Data is extracted from the data file attributes and placed into
        the correct projection (4326) using the lat_lon_4326 method.
        The lat_lon_4326 method returns a bounding box in the following
        format [East,South,West,North].
        """
        FLOAT_REGEX = r"\d+\.\d+"
        coords = self.attributes["StructMetadata.0"].split("\n\t\t")[5:7]
        coords = [
            float(elem)
            for coord in coords
            for elem in re.findall(FLOAT_REGEX, coord)
        ]
        coords = [coords[1], coords[0], coords[3], coords[2]]
        bounding_box = self.lat_lon_4326(coords)
        self.root["Spatial"]["HorizontalSpatialDomain"] = {"Geometry": {}}
        bounding_box_dict = {}
        bounding_box_dict["BoundingRectangle"] = {}
        bounding_box_dict["WestBoundingCoordinate"] = bounding_box[2]
        bounding_box_dict["BoundingRectangle"][
            "EastBoundingCoordinate"
        ] = bounding_box[0]
        bounding_box_dict["BoundingRectangle"][
            "NorthBoundingCoordinate"
        ] = bounding_box[3]
        bounding_box_dict["BoundingRectangle"][
            "SouthBoundingCoordinate"
        ] = bounding_box[1]
        self.root["Spatial"]["HorizontalSpatialDomain"][
            "Geometry"
        ] = bounding_box_dict

    def move_to_S3(self, bucket_name, report_name):
        """
        If the metadata file is able to be successfully written by the
        processing code, we move the data to S3 using the assumed role
        from GCC. This is required for the bucket access policy to be
        applied correctly such that LPDAAC has read/get access.
        """
        object_name = "/".join([self.product, "metadata", report_name])
        print(object_name)
        creds = update_credentials.assume_role(
            "arn:aws:iam::611670965994:role/gcc-S3Test", "brian_test"
        )
        client = boto3.client(
            "s3",
            aws_access_key_id=creds["AccessKeyId"],
            aws_secret_access_key=creds["SecretAccessKey"],
            aws_session_token=creds["SessionToken"],
        )
        try:
            client.upload_file(report_name, bucket_name, object_name)
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def post_processing(self):
        """
        This method converts the dictionary to xml and removes the item tag
        for fields with a list of elements (e.g. AdditionalAttribute).
        This also returns a status message to the main function that is
        outputted to the screen with the file name.
        """

        file_name = self.data_file.replace("hdf", "cmr.xml")
        with open(file_name, "w") as xml_metadata:
            xml_file = dicttoxml(
                {"Granule": self.root}, root=False, attr_type=False
            ).decode("utf-8")
            # Hacky way of getting rid of item tag
            xml_file = xml_file.replace("<item>", "")
            xml_file = xml_file.replace("</item>", "")
            xml_metadata.write(xml_file)
        result = self.move_to_S3(self.object.bucket_name, file_name)
        if result is True:
            os.remove(file_name)

        return {True: "Success", False: "Failed"}[result]
