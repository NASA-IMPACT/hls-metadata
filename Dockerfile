FROM osgeo/gdal:ubuntu-full-latest

RUN apt-get update
RUN apt-get install python3-pip -y
 
# RUN pip install --upgrade numpy && pip install --ignore-installed pyparsing
RUN pip3 install rasterio==1.1.3 shapely --no-binary rasterio
RUN pip3 install tox
RUN apt-get install build-essential python3-dev python3-numpy libhdf4-dev -y

COPY ./ ./hls-metadata

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["cd hls-metadata && tox -r"]


