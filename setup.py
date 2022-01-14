from setuptools import find_packages, setup

setup(
    name="metadata_creator",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click~=7.1.0",
        "numpy",
        "pyhdf",
        "pyproj==2.6.1",
        "rasterio",
        "shapely",
        "lxml",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-cov",
            "black",
            "flake8",
            "isort",
        ],
        "dev": [
            "pytest",
            "black",
            "flake8",
            "isort",
            "pre-commit",
            "pre-commit-hooks",
        ],
    },
    entry_points={
        "console_scripts": [
            "create_metadata=metadata_creator.metadata_creator:create_metadata",
        ]
    },
)
