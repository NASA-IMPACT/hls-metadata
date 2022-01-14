import os
from doctest import Example

import pytest
from lxml import etree
from lxml.doctestcompare import LXMLOutputChecker

from metadata_creator.metadata_creator import Metadata

current_dir = os.path.dirname(__file__)
metadata_dir = os.path.join(current_dir, "data")
data_dir = "/hls-testing_data"


def sortxml(xml):
    doc = etree.XML(xml, etree.XMLParser(remove_blank_text=True))
    for parent in doc.xpath("//*[./*]"):
        parent[:] = sorted(parent, key=lambda x: x.tag)
    return etree.tostring(doc, pretty_print=True)


def assert_xml_equals(reference, result):
    """Compare if XML documents are equal except formatting."""
    checker = LXMLOutputChecker()
    if not checker.check_output(reference, result, 0):
        message = checker.output_difference(Example("", reference), result, 0)
        pytest.fail(message)


def test_S30_metadata():
    test_granule = "HLS.S30.T01LAH.2020097T222759.v1.5"
    with open(
        os.path.join(
            metadata_dir,
            test_granule + ".xml",
        ),
        "r",
    ) as file:
        wanted = file.read()

    metadata = Metadata(
        os.path.join(
            data_dir,
            test_granule + ".hdf",
        )
    ).xml

    # Strip times which will be different when comparing to test output
    # Use pretty_print to make sure xml is formatted the same
    def strip_times(xml, tags):
        root = etree.fromstring(xml)
        for tag in tags:
            etree.strip_elements(root, tag)
        return etree.tostring(root, pretty_print=True)

    tags = ["InsertTime", "LastUpdate"]
    wanted = strip_times(wanted, tags)
    metadata = strip_times(metadata, tags)
    assert_xml_equals(str(wanted), str(metadata))


def test_L30_metadata():
    test_granule = "HLS.L30.39TVF.2020158.165.v1.5"
    with open(
        os.path.join(
            metadata_dir,
            test_granule + ".xml",
        ),
        "r",
    ) as file:
        wanted = file.read()

    metadata = Metadata(
        os.path.join(
            data_dir,
            test_granule + ".hdf",
        )
    ).xml

    # Strip times which will be different when comparing to test output
    # Use pretty_print to make sure xml is formatted the same
    def strip_times(xml, tags):
        root = etree.fromstring(xml)
        for tag in tags:
            etree.strip_elements(root, tag)
        return etree.tostring(root, pretty_print=True)

    tags = ["InsertTime", "LastUpdate"]
    wanted = strip_times(wanted, tags)
    metadata = strip_times(metadata, tags)
    assert_xml_equals(str(wanted), str(metadata))


def test_S30_bounding_box():
    test_granule = "HLS.S30.T48UXF.2020274T041601.v1.5"
    with open(
        os.path.join(
            metadata_dir,
            test_granule + ".xml",
        ),
        "r",
    ) as file:
        wanted = file.read()

    metadata = Metadata(
        os.path.join(
            data_dir,
            test_granule + ".hdf",
        )
    ).xml

    # Strip times which will be different when comparing to test output
    # Use pretty_print to make sure xml is formatted the same
    def strip_times(xml, tags):
        root = etree.fromstring(xml)
        for tag in tags:
            etree.strip_elements(root, tag)
        return etree.tostring(root, pretty_print=True)

    tags = ["InsertTime", "LastUpdate"]
    wanted = strip_times(wanted, tags)
    metadata = strip_times(metadata, tags)
    assert_xml_equals(str(wanted), str(metadata))
