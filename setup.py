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
        "shapely==1.8a1",
        "lxml",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-cov",
            "flake8",
            "isort",
        ],
        "dev": [
            "pytest",
            "black==20.8b1",
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
