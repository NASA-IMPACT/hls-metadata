FROM 018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-base:latest
COPY . ${SRC_DIR}/hls-metadata
WORKDIR ${SRC_DIR}/hls-metadata
RUN pip install --upgrade numpy && pip install --ignore-installed pyparsing
RUN pip install rasterio shapely --no-binary rasterio
RUN pip install -e .['test']
WORKDIR /data
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["pytest ${SRC_DIR}/hls-metadata"]
