#hls-metadata-brian - creates metadata for HLS

Installation:
Installation requires python development libraries and hdf4 binaries. On an Ubuntu/Debian system they can be installed with the following.
```bash
sudo apt-get install build-essential python3-dev python-dev libhdf4-dev # For Python 3

```
```bash
pip install .
```

This will install both the metadata_creator package as well as install a create_metadata and run_metadata executable on your path.

Examle Usage
'''bash
create_metadata file.hdf >metadata.xml # Send XML metadata to stdout
create_metadata file.hdf --save metadata.xml # Use --save argument to set destination
create_metadata file.hdf --s3 # Save to default hls-global bucket location
create_metadata file.hdf --s3 bucket/key

run_metadata # runs the run_metadata script
'''
