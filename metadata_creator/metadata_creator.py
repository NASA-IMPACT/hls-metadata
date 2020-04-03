import os
import datetime
import re
import json
import boto3
import update_credentials
import click
import logging
from collections import OrderedDict
from pyhdf.SD import SD
import rasterio
from rasterio import features
from shapely.geometry import Polygon, MultiPolygon
from shapely import wkt, ops

try:
    from pyproj import CRS, transform
except ImportError:
    from pyproj import Proj, transform
from botocore.exceptions import ClientError
from lxml import etree

current_dir = os.path.dirname(__file__)
util_dir = os.path.join(current_dir, "templates")


def split_at_dateline(poly):
    shifted = []
    for pt in list(poly.boundary.coords):
        if pt[0] < 0:
            lon = pt[0] + 360
        else:
            lon = pt[0]
        shifted.append([lon, pt[1]])

    poly_shift = Polygon(shifted)
    line = wkt.loads("LINESTRING(180 -90, 180 90)")

    merged = ops.linemerge([poly_shift.boundary, line])
    borders = ops.unary_union(merged)
    polygons = ops.polygonize(borders)

    new_poly = []
    for p in polygons:
        print("Shift Polygon: ", str(p))
        deshifted = []
        for pt in list(p.boundary.coords):
            if p.bounds[2] > 180:
                lon = pt[0] - 360
            else:
                lon = pt[0]
            deshifted.append([lon, pt[1]])
        new_poly.append(Polygon(deshifted))

    split_poly = MultiPolygon(new_poly)
    return split_poly


class Metadata:
    def __init__(self, data_path, bucket="hls-global"):
        # initialize the granule level metadata file
        self.root = OrderedDict()
        self.root["GranuleUR"] = None
        self.root["InsertTime"] = None
        self.root["LastUpdate"] = None
        self.root["Collection"] = {}
        self.root["DataGranule"] = {}
        self.root["Temporal"] = {}
        self.root["Spatial"] = {}
        self.root["Platforms"] = []
        # self.root["OnlineAccessURLs"] = []
        # self.root["OnlineResources"] = []
        # self.root["AssociatedBrowseImageUrls"] = []
        self.root["AdditionalAttributes"] = []

        self.data_path = data_path
        self.data_file = os.path.basename(self.data_path)
        self.product = self.data_file.split(".")[1]
        self.report_name = self.data_file.replace("hdf", "cmr.xml")
        self.bucket = bucket
        self.generate()

    def generate(self):
        """
        Public: Main method to run. Extract metadata as xml
        Examples
          m = Metadata('<file path>')
          m.xml

        Returns output as xml.
        """
        self.extract_attributes()
        self.template_handler()
        self.attribute_handler()
        self.data_granule_handler()
        self.time_handler()
        self.bounding_poly_handler()
        return

    def extract_attributes(self):
        # extract the attributes from the data file
        try:
            granule = SD(self.data_path, 1)
        except TypeError:
            granule = SD(self.data_path.encode("utf-8"), 1)
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
        with open(
            os.path.join(util_dir, self.product + ".json"), "r"
        ) as template_file:
            template = json.load(template_file, object_pairs_hook=OrderedDict)
        template = template[self.product]
        spacecraft_name = self.attributes.get("SPACECRAFT_NAME")
        platform = "LANDSAT-8" if spacecraft_name is None else spacecraft_name
        self.root["Collection"]["DataSetId"] = template["DataSetId"]
        self.data_format = self.data_file.split(".")[-1]
        self.root["Platforms"].append(template[platform])
        self.root["AdditionalAttributes"] = template["AdditionalAttributes"]
        self.root["GranuleUR"] = self.data_file.replace(
            "." + self.data_format, ""
        )

    def attribute_handler(self):
        """
        Loops through the attributes in the template file.
        Some of the additional attribute metadata names are inconsistent
        with the names in the hdf file. The attribute_mapping json file
        provides this mapping so that the appropriate value can be added
        for each of the additional attribute fields.
        """
        with open(
            os.path.join(util_dir, self.product + "_attribute_mapping.json"),
            "r",
        ) as attribute_file:
            attribute_mapping = json.load(
                attribute_file, object_pairs_hook=OrderedDict
            )
        for attribute in self.root["AdditionalAttributes"]:
            attribute_name = attribute_mapping[attribute["Name"]]
            value = self.attributes.get(attribute_name, None)
            datatype = attribute["DataType"]
            del attribute["DataType"]
            del attribute["Description"]
            if value is None and attribute.get("Values", None) is None:
                if attribute["Name"] == "MGRS_TILE_ID":
                    attribute["Values"] = {
                        "Value": self.data_file.split(".")[2][1:]
                    }
                else:
                    missing_values = {
                        "INT": -9999,
                        "FLOAT": -9999.9,
                        "STRING": "Not Available",
                    }
                    attribute["Values"] = {"Value": missing_values[datatype]}
                continue
            elif attribute.get("Values", None) is not None:
                continue

            values = None
            if isinstance(value, list):
                values = value

            if (
                not values
                and datatype in ("FLOAT", "INT")
                and "," in str(value)
            ):
                values = value.split(",")

            if not values:
                values = [value]

            if datatype == "FLOAT" and value is not None:
                if values:
                    values = [round(float(v), 8) for v in values]
                else:
                    value = round(float(value), 8)
            attribute["Values"] = values

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
        data_granule = OrderedDict()
        data_granule["SizeMBDataGranule"] = int(
            os.path.getsize(self.data_path) / 1024
        )
        data_granule["ProducerGranuleId"] = self.data_file.replace(
            extension, ""
        )
        data_granule["DayNightFlag"] = "DAY"
        data_granule["ProductionDateTime"] = production_date
        data_granule["LocalVersionId"] = self.data_file[-7:].replace(
            "." + self.data_format, ""
        )
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
        self.root["InsertTime"] = datetime.datetime.utcnow().strftime(
            time_format
        )
        # This needs to be updated to last update time of file
        self.root["LastUpdate"] = datetime.datetime.utcnow().strftime(
            time_format
        )

        sensing_time = self.attributes["SENSING_TIME"].split(";")
        temporal = self.root["Temporal"]
        temporal["RangeDateTime"] = OrderedDict()
        sensing_time1 = sensing_time[0].split('+')[0].replace(" ","")[:-2]
        sensing_time2 = sensing_time[-1].split('+')[-1].replace(" ","")[:-2]
        time1 = datetime.datetime.strptime(
            sensing_time1, time_format[:-1]
        )
        time2 = datetime.datetime.strptime(
            sensing_time2, time_format[:-1]
        )
        temporal["RangeDateTime"]["BeginningDateTime"] = time1.strftime(
            time_format
        )
        temporal["RangeDateTime"]["EndingDateTime"] = time2.strftime(
            time_format
        )
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

        # deal with older and newer versions of pyproj
        try:
            hdf_proj = CRS.from_epsg(3857)
            reproj_proj = CRS.from_epsg(4326)
        except NameError:
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
        bounding_box = [round(c, 8) for c in bounding_box]
        self.root["Spatial"]["HorizontalSpatialDomain"] = {"Geometry": {}}
        bounding_box_dict = OrderedDict()
        bounding_box_dict["WestBoundingCoordinate"] = bounding_box[2]
        bounding_box_dict["NorthBoundingCoordinate"] = bounding_box[3]
        bounding_box_dict["EastBoundingCoordinate"] = bounding_box[0]
        bounding_box_dict["SouthBoundingCoordinate"] = bounding_box[1]
        self.root["Spatial"]["HorizontalSpatialDomain"]["Geometry"][
            "BoundingRectangle"
        ] = bounding_box_dict

    def bounding_poly_handler(self):
        path = "HDF4_EOS:EOS_GRID:" + self.data_path + ":Grid:Fmask"
        points = []
        geometries = []
        with rasterio.open(path) as src:

            for record in features.dataset_features(
                src,
                bidx=1,
                sampling=10,
                band=False,
                as_mask=True,
                with_nodata=False,
                geographic=True,
                precision=8,
            ):
                geom = record["geometry"]
                poly = Polygon(geom["coordinates"][0]).simplify(
                    0.01, preserve_topology=True
                )
                if poly.bounds[0] < 0 and poly.bounds[1] >= 0:
                    mpoly = split_at_dateline(poly)
                else:
                    mpoly = MultiPolygon([poly])

                for p in mpoly:
                    points = []
                    for x, y in p.exterior.coords[:-1]:
                        points.append(
                            OrderedDict(
                                {"PointLongitude": x, "PointLatitude": y}
                            )
                        )
                    gpoly = {"Boundary": points}
                    geometries.append(gpoly)

        spatial = OrderedDict({"HorizontalSpatialDomain": {"Geometry": geometries}})

        self.root["Spatial"] = spatial

    def save_to_S3(self):
        """
        If the metadata file is able to be successfully written by the
        processing code, we move the data to S3 using the assumed role
        from GCC. This is required for the bucket access policy to be
        applied correctly such that LPDAAC has read/get access.
        """

        object_name = "/".join([self.product, "metadata", self.report_name])
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
            client.put_object(
                Bucket=self.bucket, Key=object_name, Body=self.xml
            )
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def save_to_file(self, output_path=None):
        if not output_path:
            output_path = self.report_name
        with open(output_path, "w") as xml_metadata:
            xml_metadata.write(self.xml)

    @property
    def json(self):
        return json.dumps(self.root, indent=2)

    @property
    def xml(self):
        """
        This method converts the dictionary to xml and removes the item tag
        for fields with a list of elements (e.g. AdditionalAttribute).
        For lists, it singularizes the key to the list to make the tag
        """
        with open(
            os.path.join(util_dir, "array_items.json"), "r"
        ) as template_file:
            template = json.load(template_file, object_pairs_hook=OrderedDict)

        def data2xml(d, name="data"):
            r = etree.Element(name)
            return etree.tostring(
                buildxml(r, d), pretty_print=True, encoding="unicode"
            )

        def buildxml(r, d):
            if isinstance(d, dict):
                for k, v in d.items():
                    s = etree.SubElement(r, k)
                    buildxml(s, v)
            elif isinstance(d, tuple) or isinstance(d, list):
                for v in d:
                    if r.tag in template:
                        tag = template[r.tag]
                    else:
                        tag = "item"
                    s = etree.SubElement(r, tag)
                    buildxml(s, v)
            elif isinstance(d, str):
                r.text = d
            else:
                r.text = str(d)
            return r

        return data2xml(self.root, "Granule")


@click.command()
@click.argument("data_path")
@click.option(
    "--outputformat",
    "-f",
    nargs=1,
    default="xml",
    help="Metadata Format (xml, json, yaml)",
)
@click.option("--save", nargs=1, help="Save Metadata to File")
@click.option("--s3", default=False, help="Save Metadata to S3")
def create_metadata(data_path, outputformat="xml", save=None, s3=False):
    """
    Extract Metadata from HDF file
    """
    md = Metadata(data_path)
    if save:
        md.save_to_file(output_path=save)
        return
    if s3:
        md.save_to_S3()
        return
    if outputformat == "json":
        print(md.json)
    elif outputformat == "yaml":
        print(md.yaml)
    else:
        print(md.xml)


if __name__ == "__main__":
    create_metadata()
