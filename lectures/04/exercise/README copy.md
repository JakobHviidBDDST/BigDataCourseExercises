# Lecture 04 - Spark

The exercises for this lecture are about Apache Spark. Apache Spark is a unified analytics engine for big data
processing, with built-in modules for streaming, SQL, machine learning, and graph processing. It can be used to process
large amounts of data in parallel on a cluster of computers.
Apache Spark is built to work on top of the Hadoop ecosystem and can be used to process data stored in HDFS, S3, or
other storage systems.

Please open issues [here](https://github.com/jakobhviid/BigDataCourseExercises/issues) if you encounter unclear
information or experience bugs in our examples!

## Exercises

### Exercise 1 - Deploying Apache Spark on Kubernetes

Before you get to play around with Apache Spark you need to deploy your Spark environment on your Kubernetes cluster. We
will be using a helm chart to deploy Spark on Kubernetes.

**Task**: Inspect the [spark-values.yaml](./spark-values.yaml) file to see how the Spark deployment is configured.

**Task**: Install the Spark Helm chart using the following command:

```bash
helm install --values spark-values.yaml spark oci://registry-1.docker.io/bitnamicharts/spark --version 9.2.10
```

**Task**: Inspect the UI of the Spark deployment and validate that there are two worker nodes alive.

```bash
kubectl port-forward svc/spark-master-svc 8080:80
```

### Exercise 2 - Running a Spark job locally and in your deployment

The first exercise is to run a Spark job that estimates pi. The program is written in Python and is an example of how to
create a Spark job that both can run on your localhost and in your Spark environment.

**Task**: Inspect the [pi-estimation.py](./pi-estimation.py) file.

**Task**: Run the [pi-estimation.py](./pi-estimation.py) file locally using Python.

**Help**: Running Spark jobs

- Using Python: ``python <SCRIPT.py> <NUMBER_OF_PARTITIONS>``
- Using `spark-submit`: ``spark-submit <SCRIPT.py> <NUMBER_OF_PARTITIONS>``
    - Have a look at the `spark-submit` documentation
      for [submitting-applications](https://spark.apache.org/docs/latest/submitting-applications.html).

**Question**: How will the number of partitions argument affect the result?

<details>
  <summary><strong>Hint</strong>: Run Spark locally</summary>

Change this line of code in [pi-estimation.py](./pi-estimation.py) to point to `SPARK_ENV.LOCAL`

  ```text
  spark = get_spark_context(app_name="Pi estimation", config=SPARK_ENV.LOCAL)
  ```

</details>

**Task**: Update the [pi-estimation.py](./pi-estimation.py) file to be executed on the inside your Kubernetes cluster.

- Does the number of partitions affect the runtime?
- How does the runtime compare to running the program locally?

<details>
  <summary><strong>Hint</strong>: Run Spark within the Kubernetes cluster</summary>

Change this line of code in [pi-estimation.py](./pi-estimation.py) to point to `SPARK_ENV.K8S`

  ```text
  spark = get_spark_context(app_name="Pi estimation", config=SPARK_ENV.K8S)
  ```

</details>

**Help**: Key differences between `python <SCRIPT.py>` and `spark-submit <SCRIPT.py>`

| **Aspect**              | `python <SCRIPT.py>`                                     | `spark-submit <SCRIPT.py>`                                               |
|-------------------------|----------------------------------------------------------|--------------------------------------------------------------------------|
| **Execution Mode**      | Local execution as a regular Python script               | Submit as a Spark job to a cluster                                       |
| **Spark Context**       | Must be created within the script                        | Created and managed by `spark-submit`                                    |
| **Cluster Integration** | Limited to local mode or simple clusters                 | Supports full integration with cluster managers (YARN, Kubernetes, etc.) |
| **Resource Management** | Limited to local machine resources                       | Managed by the cluster, scalable                                         |
| **Use Case**            | Development and testing locally                          | Production and large-scale distributed jobs                              |
| **Ease of Setup**       | Very easy; no additional setup required                  | Requires setup of cluster configuration and environment                  |
| **Dependencies**        | Must be managed manually in the script                   | Can include dependencies via `--packages` or `--jars` options            |
| **Error Handling**      | Errors shown in the console directly                     | Errors logged in cluster logs, more difficult to debug remotely          |
| **Logging**             | Logs output to console                                   | Logs managed by cluster manager, accessible via web UI or files          |
| **Deployment Modes**    | Supports only local mode                                 | Supports local, client, and cluster deployment modes                     |
| **Job Configuration**   | Configuration is hard-coded or via environment variables | Can pass configurations via command-line options                         |
| **Output and Results**  | Printed to console                                       | Can be redirected to files, databases, or external storage               |

### Exercise 3 - Analyzing files using Spark jobs

The previous program you ran was estimating pi. This program only used compute resources and in this exercise you will
run a Spark job that will read a file and count the occurrences of different words in the file. You will be analyzing
the alice in wonderland text
from [lecture 2 exercise 3](../02/README.md#exercise-3---uploading-alice-in-wonderland-to-hdfs).

**Task**: Ensure the [alice in wonderland](https://www.gutenberg.org/files/11/11-0.txt) file is within your HDFS
cluster. If not upload the file to HDFS.

**Task**: Inspect the [word-count.py](./word-count.py). The program counts the occurrences of all unique "words" in the
input file.

**Task**: Try to visualize the [DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph) this program will create.

**Help**:

- Take a look [here](https://stackoverflow.com/a/30685279/9698208) to better understand how the DAG is created for the
  Spark program.
- You are able to get other examples of Spark programs [here](https://spark.apache.org/examples.html).

**Task**: Run the program locally and in the cluster pointing towards different input files.

```bash
spark-submit word-count.py
```

**Notice**:You can read about the word count program from Apache Spark [here](https://spark.apache.org/examples.html)
and [here](https://github.com/apache/spark/blob/c1b12bd56429b98177e5405900a08dedc497e12d/examples/src/main/python/wordcount.py).

### Exercise 4 - Average sample values from JSON files stored in HDFS

Let us assume that you have a dataset of sample records stored in HDFS. The dataset is stored in JSON format and
contains defined by the [exercise 10 from lecture 02](../02/README.md#exercise-10---create-six-fictive-data-sources).

In this exercise you will run a Spark job that will read all the JSON files and computes the average value of the
`payload.modality` field for each station.

**Task**: Inspect the [avg-modalities.py](./avg-modalities.py).

**Task**: Ensure you have records stored in HDFS on the proper location. If not upload the records to HDFS
using [exercise 4 from lecture 03](./../03/README.md#exercise-4---produce-messages-to-kafka-using-python)
and [exercise 7 from lecture 3](../03/README.md#exercise-7---kafka-connect-and-hdfs)

**Task**: Run the Spark application on the cluster. What is the `payload.modality` average value for each station?

```bash
spark-submit avg-modalities.py
```

### Exercise 5 - Average sample values from Avro files stored in HDFS (optional)

Let us assume that you have a dataset of sample records stored in HDFS. The dataset is stored in Avro format and
contains defined by the [exercise 10 from lecture 02](../02/README.md#exercise-10---create-six-fictive-data-sources)

In this exercise you will run a Spark job that will read all the Avro files and computes the average value of the
`payload.modality` field for each station.

**Task**: Inspect the [avg-modalities-avro.py](./avg-modalities-avro.py).

**Task**: Ensure you have records stored in HDFS on the proper location. If not upload the records to HDFS
using [exercise 10 from lecture 02](../02/README.md#exercise-10---create-six-fictive-data-sources)

**Task**: Run the Spark application on the cluster. This should produce the same results as
in [Exercise 4](#exercise-4---average-sample-values-from-json-files-stored-in-hdfs)

```bash
spark-submit --packages org.apache.spark:spark-avro_2.12:3.5.2 avg-modalities-avro.py
```

### Exercise 6 - Running Spark Streaming Jobs - Kafka

The objective of this exercise is to create a Spark streaming job that reads from a Kafka topic. This exercise requires
to have a Kafka producer which produces records in the given topic. For convenience, we recommend revisiting
the [exercise 4 from lecture 03](./../03/README.md#exercise-4---produce-messages-to-kafka-using-python).

**Task**: Create a streaming query that calculates the running mean of the six different stations (`payload.sensor_id`)
produced to the Kafka topic `INGESTION`.

**Help**: You need to complete the query inside the [process-streaming.py](process-streaming.py) file.
**Notice**: You need to append additional packages as arguments to run the Spark streaming application to read from
kafka. You can enable an interactive Spark streaming prompt using `pyspark` or submitting your final Spark application
using `spark-submit` as demonstrated below:

```bash
pyspark --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.2 
```

```bash
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.2 process-streaming.py
```

**Task**: Run your Spark streaming application and validate that the running means of `payload.modality` field is close
to the calculated values in [exercise 4](README.md#exercise-4---average-sample-values-from-json-files-stored-in-hdfs).

**Important note**: There is no correct solution for this exercise. You may find inspiration in the following links to
complete the streaming query:

- [Structured Streaming Programming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#structured-streaming-programming-guide)
- [Operations on streaming DataFrames/Datasets](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#operations-on-streaming-dataframesdatasets)
- [Structured Streaming + Kafka Integration Guide](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html#structured-streaming-kafka-integration-guide-kafka-broker-versio)

## Step-by-step guide to clean up

You will be using HDFS, Kafka and the interactive container in next lecture. However, if you will clean up the
resources created in this lecture, you can follow the steps below:

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

- Today's exercises.
    1. `helm delete spark`
- `cd` into the `lecture/03` folder in the repository.
    1. `kubectl delete -f redpanda.yaml`
    1. `kubectl delete -f kafka-schema-registry.yaml`
    1. `kubectl delete -f kafka-connect.yaml`
    1. `kubectl delete -f kafka-ksqldb.yaml`
    1. `helm uninstall kafka`
    1. `kubectl delete pvc data-kafka-controller-0 \
      data-kafka-controller-1 \
      data-kafka-controller-2
        `
- `cd` into the `services/interactive` folder in the repository.
    1. `kubectl delete -f interactive.yaml`
- cd into the `services/hdfs` folder in the repository.
    1. `kubectl delete -f hdfs-cli.yaml` (if used)
    1. `kubectl delete -f datanodes.yaml`
    1. `kubectl delete -f namenode.yaml`
    1. `kubectl delete -f configmap.yaml`

You can get a list of the pods and services to verify that they are deleted.

- `kubectl get all`
