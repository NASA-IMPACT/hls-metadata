import os
from xmltodict import parse
from metadata_creator.metadata_creator import Metadata

current_dir = os.path.dirname(__file__)
test_dir = os.path.join(current_dir, "data")


def test_metadata():
    with open(
        os.path.join(
            test_dir, "HLS.S30.T02LNH.20200224.20200224T230359.v1.5.cmr.xml"
        ),
        "r",
    ) as file:
        wanted = parse(file.read())

    metadata = parse(
        Metadata(
            os.path.join(
                test_dir, "HLS.S30.T02LNH.20200224.20200224T230359.v1.5.hdf"
            )
        ).xml
    )

    # InsertTime is going to be different, so unset
    del wanted["Granule"]["InsertTime"]
    del metadata["Granule"]["InsertTime"]

    assert 'Granule' in metadata
    assert wanted == metadata
