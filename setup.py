from setuptools import setup, find_packages

setup(
    name="metadata_creator",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "numpy",
        "pyhdf",
        "pyproj",
        "rasterio",
        "shapely",
    ],
    extras_require={"dev": ["flake8", "black"], "test": ["pytest", "lxml"]},
    package_data={"metadata_creator": ["templates/*.json"]},
    entry_points={
        "console_scripts": [
            "create_metadata=metadata_creator.metadata_creator:create_metadata",
        ]
    },
)
