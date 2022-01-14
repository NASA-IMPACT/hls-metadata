FROM osgeo/gdal:ubuntu-full-3.0.3

# Required for click with Python 3.6
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN apt-get update
RUN apt-get install python3-pip python3-venv git -y

 
RUN pip3 install rasterio==1.1.3 shapely --no-binary rasterio
RUN apt-get install build-essential python3-dev python3-numpy libhdf4-dev -y
RUN pip3 install tox tox-venv
RUN pip3 install --upgrade setuptools
RUN git clone https://github.com/NASA-IMPACT/hls-testing_data

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["cd hls-metadata && tox -r"]


