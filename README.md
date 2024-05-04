# hls-metadata
## Generate CMR metdata for HLS products

## Example Usage
```bash
create_metadata file.hdf > metadata.xml # Send XML metadata to stdout
create_metadata file.hdf --save metadata.xml # Use --save argument to set destination
```

### Requirements
The use of rasterio for HDF does not allow for the regular pip install of rasterio using wheels. It requires a preinstalled gdal version that supports HDF4 installed on the system and install rasterio using
```
pip install rasterio --no-binary rasterio
```

Installation requires python development libraries and hdf4 binaries. On an Ubuntu/Debian system they can be installed with the following.
```bash
sudo apt-get install build-essential python3-dev python-dev libhdf4-dev # For Python 3

```

### Tests
Run Tests on Docker
```bash
docker build -t hls-metadata . &&  docker run -v $PWD:/hls-metadata hls-metadata
```


### Development
Because of the C lib dependencies on HDF4, developing this application is easisest in Docker.  To use the development container run
```bash
docker compose up --build
docker run -it -v $PWD:/hls-metadata hls-metadata /bin/bash
```
At the container's shell prompt
```bash
cd hls-metadata
tox -e dev
source devenv/bin/activate
```

To interactively test the application in the container
```bash
cd hls-metadata
pip3 install -e .
create_metadata ../hls-testing_data/HLS.S30.T01LAH.2020097T222759.v1.5.hdf --save HLS.S30.T01LAH.2020097T222759.v1.5.xml
```

To run the unit tests
```bash
docker compose up --build
```
