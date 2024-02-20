from setuptools import find_packages
from setuptools import setup

setup(
    name="alluxiofs",
    version="0.1",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "fsspec",
    ],
    extras_require={"tests": ["pytest"]},
    python_requires=">=3.8",
    maintainer="Lu Qiu",
    maintainer_email="luqiujob@gmail.com",
    entry_points={
        "fsspec.specs": [
            "alluxio=alluxiofs.AlluxioFileSystem",
        ],
    },
)
