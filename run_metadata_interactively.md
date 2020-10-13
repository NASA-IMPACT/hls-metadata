docker run -it hls-metadata /bin/bash
cd hls-metadata
pip3 install .
create_metadata ../hls-testing_data/HLS.S30.T01LAH.2020097T222759.v1.5.hdf --save HLS.S30.T01LAH.2020097T222759.v1.5.cmr.xml
create_metadata ../hls-testing_data/HLS.L30.39TVF.2020158.165.v1.5.hdf --save HLS.L30.39TVF.2020158.165.v1.5.cmr.xml
