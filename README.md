# Alluxio FileSystem

This quickstart shows how you can use the FSSpec interface to connect to [Alluxio](https://github.com/Alluxio/alluxio).
For more information on what to expect, please read the blog [Accelerate data loading in large scale ML training with Ray and Alluxio](https://www.alluxio.io/blog/accelerating-data-loading-in-large-scale-ml-training-with-ray-and-alluxio/).

## Dependencies

### A running Alluxio server with ETCD membership service

Alluxio version >= 309

Launch Alluxio clusters with the example configuration
```config
# only one master, one worker are running in this example
alluxio.master.hostname=localhost
alluxio.worker.hostname=localhost

# Critical properties for this example
# UFS address (e.g., the src of data to cache), change it to your bucket
alluxio.dora.client.ufs.root=s3://example_bucket/datasets/
# storage dir
alluxio.worker.page.store.dirs=/tmp/page_ufs
# size of storage dir
alluxio.worker.page.store.sizes=10GB
# use etcd to keep consistent hashing ring
alluxio.worker.membership.manager.type=ETCD
# default etcd endpoint
alluxio.etcd.endpoints=http://localhost:2379
# number of vnodes per worker on the ring
alluxio.user.consistent.hash.virtual.node.count.per.worker=5

# Other optional settings, good to have
alluxio.job.batch.size=200
alluxio.master.journal.type=NOOP
alluxio.master.scheduler.initial.wait.time=10s
alluxio.network.netty.heartbeat.timeout=5min
alluxio.underfs.io.threads=50
```

### Python Dependencies

Python in range of [3.8, 3.9, 3.10]
ray >= 2.8.2
fsspec released after 2023.6

#### Install fsspec implementation for underlying data storage

Alluxio fsspec acts as a cache on top of an existing underlying data lake storage connection.
The fsspec implementation corresponding to the underlying data lake storage needs to be installed.
In the below Alluxio configuration example, Amazon S3 is the data lake storage where the dataset is read from.

To connect to an existing underlying storage, there are two requirements
- Install the underlying storage fsspec
  - For all [built-in storage fsspec](https://filesystem-spec.readthedocs.io/en/latest/api.html#built-in-implementations), no extra python libraries are needed to be installed.
  - For all [third-party storage fsspec](https://filesystem-spec.readthedocs.io/en/latest/api.html#other-known-implementations), the third-party fsspec python libraries are needed to be installed.
- Set credentials for the underlying data lake storage

Example: Deploy S3 as the underlying data lake storage
[Install third-party S3 fsspec](https://s3fs.readthedocs.io/en/latest/)

```commandline
pip install s3fs
```
#### Install alluxiofs

Directly install the latest published alluxiofs
```
pip install alluxiofs
```

[Optional] Install from the source code
```commandline
git clone git@github.com:fsspec/alluxiofs.git
cd alluxiofs && python3 setup.py bdist_wheel && \
     pip3 install dist/alluxiofs-<alluxio_fs_version>-py3-none-any.whl
```

## Running a Hello World Example

### Load the dataset

#### Load dataset using Alluxio CLI load command

````commandline
bin/alluxio job load --path s3://example_bucket/datasets/ --submit
````
This will trigger a load job asynchronously with a job ID specified. You can wait until the load finishes or check the progress of this loading process using the following command:

````commandline
bin/alluxio job load --path s3://example_bucket/datasets/ --progress
````

#### Load dataset using Alluxio Python filesystem

In the python script
```
from alluxio import AlluxioPythonFileSystem

alluxio_py = AlluxioPythonFileSystem(etcd_hosts=args.etcd_hosts)
alluxio_py.load(path="s3://example_bucket/datasets/")
```

Alluxio Python libraries also support `submit_load`, `load_progress`, and `stop_load` commands.

### Create a AlluxioFS (backed by S3)

Create the Alluxio Filesystem with data backed in S3

```
import fsspec
from alluxiofs import AlluxioFileSystem

# Register Alluxio to fsspec
fsspec.register_implementation("alluxio", AlluxioFileSystem, clobber=True)

# Create Alluxio filesystem
alluxio = fsspec.filesystem("alluxio", etcd_hosts="localhost", etcd_port=2379, target_protocol="s3")
```

If `Alluxio_py` is already inited, Alluxio fsspec can ingest the underlying Alluxio Python filesystem directly
```
import fsspec
from alluxio import AlluxioPythonFileSystem
from alluxiofs import AlluxioFileSystem

fsspec.register_implementation("alluxio", AlluxioFileSystem, clobber=True)
alluxio_py = AlluxioPythonFileSystem(etcd_hosts=args.etcd_hosts)
alluxio = fsspec.filesystem("alluxio", alluxio_fs=alluxio_py, target_protocol="s3")
```

### Run Alluxio FileSystem operations

Similar to [fsspec examples](https://filesystem-spec.readthedocs.io/en/latest/usage.html#use-a-file-system) and [alluxiofs](https://github.com/fsspec/alluxiofs/blob/main/tests/test_alluxio_fsspec.py) examples.
Note that all the read operations can only succeed if the parent folder has been loaded into Alluxio.
```
# list files
contents = alluxio_fs.ls("s3://apc999/datasets/nyc-taxi-csv/green-tripdata/", detail=True)

# Read files
with alluxio_fs.open("s3://apc999/datasets/nyc-taxi-csv/green-tripdata/green_tripdata_2021-01.csv", "rb") as f:
    data = f.read()
```

### Running an example with Ray

```
import fsspec
import ray
from alluxiofs import AlluxioFileSystem

# Register the Alluxio fsspec implementation
fsspec.register_implementation("alluxio", AlluxioFileSystem, clobber=True)
alluxio = fsspec.filesystem(
  "alluxio", etcd_hosts="localhost", target_protocol="s3"
)

# Pass the initialized Alluxio filesystem to Ray and read the NYC taxi ride data set
ds = ray.data.read_csv("s3://example_bucket/datasets/example.csv", filesystem=alluxio)

# Get a count of the number of records in the single CSV file
ds.count()

# Display the schema derived from the CSV file header record
ds.schema()

# Display the header record
ds.take(1)

# Display the first data record
ds.take(2)

# Read multiple CSV files:
ds2 = ray.data.read_csv("s3://apc999/datasets/csv_dir/", filesystem=alluxio)

# Get a count of the number of records in the twelve CSV files
ds2.count()

# End of Python example
```
