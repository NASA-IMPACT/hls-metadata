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

This will install both the metadata_creator package as well as install a create_metadata and run_metadata executable on your path.

Examle Usage
```bash
create_metadata file.hdf > metadata.xml # Send XML metadata to stdout
create_metadata file.hdf --save metadata.xml # Use --save argument to set destination
```

Run Tests on Docker
```bash
docker build -t hls-metadata .
docker run
```
