FROM 018923174646.dkr.ecr.us-west-2.amazonaws.com/hls-sentinel:latest
COPY . ${SRC_DIR}/hls-metadata
WORKDIR ${SRC_DIR}/hls-metadata
RUN pip install --upgrade awscli numpy && pip install --ignore-installed pyparsing
RUN pip install -e .['test']

ENTRYPOINT ["/bin/sh", "-c"]
CMD ["pytest"]