# Lecture 02 - HDFS and different file formats

The exercises for this week's lecture will be about HDFS and file formats. You will be creating a HDFS cluster and interacting with it in different ways.

Please open issues [here](https://github.com/jakobhviid/BigDataCourseExercises/issues) if you encounter unclear information or experience bugs in our examples!

## Attach Visual Studio Code to a running container in Kubernetes

For progressing in today's exercises we recommend you to look into attaching Visual Studio Code to a running container
in Kubernetes. This will shorten the development time of services that depend on resources inside Kubernetes.
Furthermore, a simpler access to the HDFS deployment in Kubernetes. You can navigate to the `services/interactive`
folder in the repository and read the [README](../../../services/interactive/README.md) file to get a better understanding
of how to attach Visual Studio Code to an interactive container in Kubernetes in this course, and you can read further
about the concept [here](https://code.visualstudio.com/docs/devcontainers/containers) to get a complete overview.

## Exercises

### Exercise 1 - Set up HDFS cluster

The initial task is to set up a HDFS cluster. Please familiarize yourself with and read
the [README](../../../services/hdfs/README.md) file in the `services/hdfs` folder of the repository. This will guide you
through the installation of an HDFS cluster on Kubernetes.

**Tasks**: Follow the instructions in the [README](../../../services/hdfs/README.md) file to deploy the HDFS cluster.

**Validate**: Verify that the HDFS cluster is up and running. There will be a single namenode and three datanodes inside
your namespace as illustrated in the chunk below.

```bash
kubectl get pods
NAME                           READY   STATUS    RESTARTS   AGE
namenode-0                     1/1     Running   0          34s
datanode-0                     1/1     Running   0          28s
datanode-1                     1/1     Running   0          19s
datanode-2                     1/1     Running   0          11s
```

### Exercise 2 - Interacting with HDFS cluster using CLI

Now that we have a HDFS cluster lets now try and use it. HDFS has a CLI tool for interacting with HDFS clusters. Because
the cluster is running inside of Kubernetes, we also need to access it from inside Kubernetes.

You need to create an interactive container using either the `apache/hadoop:3` image or the image described in
the [README](../../../services/interactive/README.md) similar to how you created an interactive container with
Ubuntu [last week](../01/README.md#exercise-6---interactive-container). The latter image contains the majority of the
logic needed for the future exercises.

**Task**: Create interactive container with the either `apache/hadoop:3` image
or [interactive.yaml](../../../services/interactive/interactive.yaml).

HDFS works much like a normal file system. The commands to interact with HDFS are also similar to the commands you would
use on a Unix system. For example, to list files and folders in a directory you would use the following command
`hdfs dfs -ls /`.

**Notice**: To use the HDFS CLI we need to specify the HDFS cluster to use if not done during the initialization of the
container. This is done by specifying the URI of the namenode when running the command. The URI is
`hdfs://namenode:9000` where `namenode` is the name of the namenode pod and `9000` is the port the namenode is listening
on. The full command to list files in the root directory would be `hdfs dfs -fs hdfs://namenode:9000 -ls /`.
Furthermore, you may need to use the `root` user when interacting with the HDFS cluster. This can be done by setting an
environment variable for the current shell session: `export HADOOP_USER_NAME=root`.

**Task**: Try to list the files inside the root directory in the HDFS cluster.
**Validate**: Verify there are no files in the root directory. The following exercises will be about creating files,
reading files, uploading files, and deleting files in HDFS. The HDFS CLI tool is used for this.

**Task**: Create a file inside the interactive container called "test.txt" and append random lines of text to the file.

<details>
  <summary><strong>Hint:</strong> Creating a file</summary>

You can simply create a file by echoing text in combination with the pipe operator:
`echo "Hello there\nNice work!" > test.txt`. Verify that the file exists by using `ls` and verify its contents using
`cat test.txt`.
</details>

To add a file to the HDFS cluster using the HDFS CLI you can use the `-put` command.

**Task**: Upload the file to the HDFS cluster

<details>
  <summary><strong>Hint:</strong> Uploading the file</summary>

`hdfs dfs -fs hdfs://namenode:9000 -put ./<filename> /<filename>`
</details>

Now that you have uploaded a file to HDFS you can try to list the files to verify that it is added. Similarly to Unix
systems you can use the `-cat` command to read the content of a given file.

**Task**: Read the contents of the file you just uploaded to HDFS

<details>
  <summary><strong>Hint:</strong> Reading the file</summary>

`hdfs dfs -fs hdfs://namenode:9000 -cat /test.txt`
</details>

**Task**: Try to delete the file from HDFS

**Hint**: Run the command `hdfs dfs` to get a list of all commands and options.

<details>
  <summary><strong>Hint:</strong> Deleting the file</summary>

`hdfs dfs -fs hdfs://namenode:9000 -rm /test.txt`
</details>

You are now able to list files and folders, read files, upload files, and delete files, using HDFS.

### Exercise 3 - Uploading Alice in Wonderland to HDFS

For the next exercises you will be working with the Alice in Wonderland book. The book can be read from this
URL [https://www.gutenberg.org/files/11/11-0.txt](https://www.gutenberg.org/files/11/11-0.txt) as raw text.

**Task**: Upload Alice in Wonderland to HDFS

**Hint**: Download using `curl -o alice-in-wonderland.txt https://www.gutenberg.org/files/11/11-0.txt`

<details>
  <summary><strong>Hint:</strong> Full example</summary>

1. `exec` into the interactive pod. You can use the pod
   from [exercise 2](#exercise-2---interacting-with-hdfs-cluster-using-cli).
2. Download Alice in Wonderland using `curl -o alice-in-wonderland.txt https://www.gutenberg.org/files/11/11-0.txt`.
3. Upload Alice in Wonderland to HDFS using `hdfs dfs -fs hdfs://namenode:9000 -put ./alice-in-wonderland.txt /`

</details>

### Exercise 4 (optional) - Mount HDFS config to interactive container

Instead of manually specifying the URI ("hdfs://namenode:9000") and making sure you connect to the correct name node you
can let the HDFS client decide this for you using a HDFS config file(s) (called "core-site.xml" and "hdfs-site.xml").

The [hdfs-cli.yaml](../../../services/hdfs/hdfs-cli.yaml) file in the `services/hdfs` folder creates a Kubernetes resource
called a ConfigMap. A ConfigMap is a resource that contains key-value pairs used for configuration. It can be used in
various ways, but we want to mount the ConfigMap as a file to the interactive container.

**Task**: Before we mount it we want to take a look at the ConfigMap and try to understand it.

**Task**: To create the interactive container and mount the config, use the
provided [hdfs-cli.yaml](../../../services/hdfs/hdfs-cli.yaml) file.

### Exercise 5 (optional) - Interacting with HDFS using Web UI

Instead of using the HDFS CLI, you can use the Web UI by port-forwarding the `namenode` service:

````bash
kubectl port-forward service/namenode 9870:9870
````

Then you can visit the [localhost:9870](http://localhost:9870)

Here you can gain information about the HDFS cluster.

Additionally, you can also perform CRUD operations on HDFS by going to this
URL [Browse Directory](http://localhost:9870/explorer.html#/)

From here you can create new folders, upload files or see the existing content of each of the folders in HDFS

### Exercise 6 - Interacting with HDFS cluster using Python

We now want to try to interact with the HDFS cluster using Python. To do this, there are a few files provided:

- [`src/client.py`](./src/client.py) - This file is used to create a HDFS client
- [`example.py`](./example.py) - This script contains examples for how to read a file and how to create a file.

**Task**: Familiarize yourself with the provided files, open the files and understand what they do.

**Tasks**:

1. Create
   an [interactive container](../../../services/interactive/README.md#attach-visual-studio-code-to-a-running-container) and
   attach Visual Studio Code to it.
1. Copy the [example.py](./example.py) and [src/client.py](./src/client.py) files to the container.
1. Install `hdfs` library using `pip install hdfs` in the container, if needed.
1. Verify the [src/client.py](./src/client.py) module uses the correct namenode.
1. Run the [example.py](./example.py) script and observe what's happening.

**Notice**: You should see that the script prints the entire Alice in Wonderland text to the console and that it then
creates a file called "write.txt" with some text.

**Further reading**: You can read more about the HDFS Python
library [here](https://hdfscli.readthedocs.io/en/latest/quickstart.html#python-bindings).

### Exercise 7 - Analyzing file and saving result in JSON format using Python

Now we know how to put files in HDFS, read files from HDFS and how to interact with HDFS. The next exercise will analyze
the data and save the results to a JSON file in HDFS.

**Task**: Open the [`counting-json.py`](./counting-json.py) file and try to understand it.

**Notice**: You should see that the script reads the Alice in Wonderland file and counts all words in the file. It then
saves the 10 most common words to a file called "word-count.json".

**Tasks**:

1. Copy the script to the interactive container.
1. Install required libraries (if needed).
1. Run the [`counting-json.py`](./counting-json.py) file.
1. Read the result directly from HDFS.
    1. What are the five most common words in Alice in Wonderland?
    1. How many times are they repeated?

### Exercise 8 - Analyzing file and saving result in Avro format using Python

Instead of saving the result as a JSON file, we will now try to save it as an Avro file.

**Task**: Open the [`counting-avro.py`](./counting-avro.py) file and try to understand it.

You should see that the script reads the Alice in Wonderland file similarly
to [exercise 6](#exercise-7---analyzing-file-and-saving-result-in-json-format-using-python). However, saving the file is
different.

**Tasks**:

1. Copy the script to the interactive container.
1. Install required libraries (if needed).
1. Run the [`counting-avro.py`](./counting-avro.py) file.
1. Read and output the result of the stored files directly from HDFS using HDFS CLI.

### Exercise 9 - Analyzing file and saving result in Parquet format using Python

We will now try to save a Parquet file to HDFS.

**Tasks**: Open the [`counting-parquet.py`](./counting-parquet.py) file and try to understand it.

**Tasks**:

1. Copy the script to the interactive container.
1. Install required libraries (if needed).
1. Run the [`counting-parquet`](./counting-parquet.py) file.
1. Read and output the result of the stored files directly from HDFS using HDFS CLI.
    1. How many column do the dataframe have?

### Exercise 10 - Create six fictive data sources

The objective of this exercise is to create a fictive data source. We want to create a Python program that enables the
simulation of multiple data sources. The fictive data source could be a sensor that measures the wattage of an
electricity line. The sample rate of the sensor will be adjustable. However, this will default to 1Hz. The ID of the
sensor must differentiate the six data streams and the valid range of the wattage for these electricity lines is between
±600MW.

You need to write a program simulates the above-mentioned information. The program at this stage may only provide a
single temporal aspect ("real_time"). However, the schema must accommodate other temporal aspects such as "edge
prediction" in the future.

You have the role of a data engineer and are required to store the samples from the sensors in HDFS for later analysis.

**Tasks**:

1. Which file format is most suitable for storing sensor samples?
1. How will you design the folder structure of your sensor samples?
1. Define a common schema for the fictive data sources
1. Write a Python program for the fictive data source that simulates the six sensors. Make use of the knowledge from
   exercises 5 to 8.
1. Write a Kubernetes deployment for your Python program.
    - How will you use the same Python program for each of the stations?
    - How will you write the Dockerfile and which image will you start from?
1. Write a short description of how you will deploy these data sources in Kubernetes together with your thoughts and
   conclusion to the two first questions in our Discord channel!

<details>
  <summary><strong>Hint:</strong> File formats</summary>

- JSON
- **Avro**
- Parquet

</details>


<details>
  <summary><strong>Hint:</strong> One folder structure</summary>

```
/data/raw/sensor_id=<Sensor ID>/temporal_aspect=<temporal aspect>/year=<year>/month=<month>/day=<day>/<filename -> correlation_id>.avro
```

</details>


<details>
  <summary><strong>Hint:</strong> One suggested schema</summary>

```json
{
  "payload": {
    "sensor_id": "1",
    // value in <"1", "2", "2", "3", "4", "5">
    "modality": 11.0,
    // value between ±600
    "unit": "MW",
    // unit for wattage
    "temporal_aspect": "real_time"
    // value in <"real_time", "edge_prediction">
  },
  "correlation_id": "23c4d380-b357-4082-9298-314ba9ef1b68",
  // correlation uuid for this sample
  "created_at": 1694375155.109314,
  // UNIX time
  "schema_version": 1
}
```

</details>

<details>
  <summary><strong>Hint:</strong> Code example(s)</summary>

You are able to find code snippets inside [`hints/data-source.py`](./hints/data-source.py) if you need suggestions and
directions for building the components of the fictive data sources.
It is now up to you to take the components and gue them together in the [`data-source.py`](./data-source.py) file.

**NB:** Use an interactive container for the development.

</details>

## Step-by-step guide to clean up

You will be using HDFS and the interactive container in next lecture. However, if you will clean up the resources
created in this lecture, you can follow the steps below:

### Automated clean up

If you have Python installed on your machine, you can use the following command to clean up all resources:

**Windows**:

````bash
python cleanup.py
````

**MacOS / Linux**:

````bash
python3 cleanup.py
````

The script will delete all resources created in the exercises.

### Manual clean up

To clean up the resources created in this lecture, you can follow the steps below:

- Today's exercises.
    1. run the follow cmd: `kubectl delete pod <name>` created
       in [exercise 2](#exercise-2---interacting-with-hdfs-cluster-using-cli).
- cd into the `services/hdfs` folder in the repository.
    1. `kubectl delete -f hdfs-cli.yaml` (if used)
    1. `kubectl delete -f datanodes.yaml`
    1. `kubectl delete -f namenode.yaml`
    1. `kubectl delete -f configmap.yaml`
- cd into the `services/interactive` folder in the repository.
    1. `kubectl delete -f interactive.yaml`

You can get a list of the pods and services to verify that they are deleted.

- `kubectl get all`
