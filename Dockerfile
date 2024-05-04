FROM osgeo/gdal:ubuntu-full-3.0.3

RUN : \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    libhdf4-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache --upgrade setuptools \
    && pip3 install --no-cache rasterio==1.1.3 tox tox-venv --no-binary rasterio \
    && :

RUN git clone https://github.com/NASA-IMPACT/hls-testing_data

WORKDIR /metadata_creator
COPY ./ ./

CMD ["tox", "-r", "-v"]
