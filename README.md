# hls-metadata
## Generate CMR metdata for HLS products

### Requirements
The use of rasterio for HDF does not allow for the regular pip install of rasterio using wheels. It requires a preinstalled gdal version that supports HDF4 installed on the system and install rasterio using
```
pip install rasterio --no-binary rasterio
```

Installation requires python development libraries and hdf4 binaries. On an Ubuntu/Debian system they can be installed with the following.
```bash
sudo apt-get install build-essential python3-dev python-dev libhdf4-dev # For Python 3

```
### Installation
Install for local testing
```bash
pip install -e .["test"]
```

This will install both the metadata_creator package as well as install a create_metadata executable on your path.

### Tests
Run Tests on Docker
```bash
docker build -t hls-metadata . &&  docker run -v $PWD:/hls-metadata hls-metadata
```

Examle Usage
```bash
create_metadata file.hdf > metadata.xml # Send XML metadata to stdout
create_metadata file.hdf --save metadata.xml # Use --save argument to set destination
```

Run Metadata Interactively in Docker
```bash
docker run -it hls-metadata /bin/bash
cd hls-metadata
pip3 install .
create_metadata ../hls-testing_data/HLS.S30.T01LAH.2020097T222759.v1.5.hdf --save HLS.S30.T01LAH.2020097T222759.v1.5.xml
create_metadata ../hls-testing_data/HLS.L30.39TVF.2020158.165.v1.5.hdf --save HLS.L30.39TVF.2020158.165.v1.5.xml
create_metadata ../hls-testing_data/HLS.S30.T48UXF.2020274T041601.v1.5.hdf --save HLS.S30.T48UXF.2020274T041601.v1.5.xml
```
