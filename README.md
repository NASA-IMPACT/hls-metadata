# hls-metadata
## Generate CMR metdata for HLS products

The use of rasterio does not allow for the regular pip install of rasterio using wheels. To run this, you must make sure that there is a gdal version that supports HDF4 installed on the system and install rasterio using
```
pip install rasterio --no-binary rasterio
```

You can run/test using the included Dockerfile which will use the system that is used in the orchestration to run.

```bash
docker build -t metadata .

 run tests
docker run metadata

# run interactively
cd tests/data
docker run -it -v $PWD:/data metadata /bin/bash
```

Installation:
Installation requires python development libraries and hdf4 binaries. On an Ubuntu/Debian system they can be installed with the following.
```bash
sudo apt-get install build-essential python3-dev python-dev libhdf4-dev # For Python 3

```

Install Python Requirements and the App
```bash
pip install .
```

This will install both the metadata_creator package as well as install a create_metadata and run_metadata executable on your path.

Examle Usage
```bash
create_metadata file.hdf > metadata.xml # Send XML metadata to stdout
create_metadata file.hdf --save metadata.xml # Use --save argument to set destination
```

Run Tests on Py 2.7 and 3.7
```bash
tox
```
