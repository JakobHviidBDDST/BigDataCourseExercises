# Lecture 05 - Distributed Data Processing and Distributed Databases

## Exercises

Please open issues [here](https://github.com/jakobhviid/BigDataCourseExercises/issues) if you encounter unclear
information or experience bugs in our examples!

### Exercise 1 - Hive

You will be setting up [Hive](https://hive.apache.org/) to read files from HDFS.
An [Apache Hive metastore](https://cwiki.apache.org/confluence/display/hive/design#Design-Metastore) service is required
in order to use the Hive connector. Hive metastore requires an SQL database to store data, so for this you will also set
up a [PostgreSQL database](https://www.postgresql.org/).

**Notice**: HDFS is a requirement for this exercise, if you do not have it in your namespace, please set it up before
you continue.

#### Hive metastore service

The Hive metastore service will be deployed with PostgreSQL.

Deploy postgres database.

```bash
helm install postgresql \
  --version=12.1.5 \
  --set auth.username=root \
  --set auth.password=pwd1234 \
  --set auth.database=hive \
  --set primary.extendedConfiguration="password_encryption=md5" \
  --repo https://charts.bitnami.com/bitnami \
  postgresql
```

**Note**: You may have to delete the `\` and newlines so that it is one command.

**Note**: If you encounter issues with creating a new table, please delete the existing PVC for Postgresql.

**Task**: Everything required to create the Hive metastore service is now ready. Apply
the [hive-metastore.yaml](./hive-metastore.yaml) file.

#### Hive

**Task**: Apply the [hive.yaml](./hive.yaml) file.

### Exercise 2 - Count words in Alice in Wonderland with Hive

We will now analyze the Alice in Wonderland text similarly to what we did
in [lecture 2 exercise 6-8](../02/README.md#exercise-7---analyzing-file-and-saving-result-in-json-format-using-python)
and [lecture 4 exercise 3](../04/README.md#exercise-3---analyzing-files-using-spark-jobs) where we read the file from
HDFS and counted words using Python and Spark respectively. But this time we will analyze the text using Hive.

#### Upload file to HDFS

Create a folder inside the HDFS (You can call it whatever you want).

**Task**: Upload Alice in Wonderland file to HDFS if not already done.

#### Connect to Hive

A service has been created for Hive. Forward port 10002 of the Hive service.

**Task**: Port-forward Web UI Hive and open the Hive Web UI webpage in your
browser [localhost:10002](http://localhost:10002/).

````bash
kubectl port-forward svc/hiveserver2 10002:10002
````

You should see at least one active session and zero open queries.

To connect to Hive's thrift API we have to port-forward the service as well. Forward port 10000 of the Hive service.

**Task**: Port-forward thrift Hive service.

````bash
kubectl port-forward svc/hiveserver2 10000:10000
````

To connect to Hive we will use [DBeaver](https://dbeaver.io/). DBeaver is a cross-platform database tool that supports
many different SQL databases.

**Task**: Download and install DBeaver.

Now that DBeaver is installed we will now create a new database connection with Hive.

**Tasks:** Open DBeaver and create a new connection database connection using the following steps:

1. Click on the "Database" tab and select "New Database Connection" from the dropdown.
1. Search for Hive and select it, then click "Next" (and install drivers if prompted to).
1. Select "Connect by: URL" and enter the following url: `jdbc:hive2://localhost:10000`.
1. Click on the "Test connection" button to make sure it works properly.
1. If it works, then click on the "Finish" button.

Now that a connection has been made to the Hive we can then begin to write SQL statements. To write SQL statements then
right-click on the connection you just made, then hover over the "SQL Editor", and then click on "Open SQL script".

**Task**: Create SQL editor

We can now begin to write SQL statements. First, we will make sure that the Hive connector has been set up.

**Task**: Show all catalogs

**Hint:** Enter the text `SHOW TABLES;`, then select it using your mouse and then press the keys `CTRL+ENTER` to execute
the SQL statement.

You should see zero tables. You now know how to create and execute SQL statements using Hive.

We will now create a new database. Then creating the database we define the name of the table and where data should be
stored.

If the location is not defined it will use the default location `/user/hive/warehouse/`

**Task**: Create a database

<details>
<summary><strong>Hint:</strong> Create database</summary>

```SQL
CREATE
DATABASE IF NOT EXISTS bucket
LOCATION 'hdfs://namenode:9000/user/hive/warehouse/'
```

Remember to enter the name of your database (`bucket`).
</details>

Now that a database has been created, we will create a table using the database. The table needs to use the format
`TextFile` and the directory of the files that will be associated with the table. You can find more information about
the formats supported by the Hive connector [here](https://trino.io/docs/current/connector/hive.html).

**Task**: Create a table using the database you just made

<details>
<summary><strong>Hint:</strong> Create table</summary>

```SQL
CREATE TABLE bucket.text
(
    line STRING
) STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/<hdfs-directory-location>';
```

Remember to enter the name of your bucket and the name of the folder that Alice in Wonderland resides in.
</details>

We can now query the files inside the specified bucket and folder. Try to select a few lines from the table you just
made.

**Task**: Run the following query `SELECT * FROM bucket.text limit 100;`.

You should see a list of the first 100 lines of the Alice in Wonderland text.

Similarly to the other exercises, we will now count the amount of words in the file, and after that we will figure out
the 10 most used words.

To count words, you can split each line by spaces, then count the words for each line and then sum the counts.

**Task**: Count the total amount of "words" in the Alice in Wonderland text.

<details>
<summary><strong>Hint:</strong> Count total words</summary>

```SQL
SELECT SUM(SIZE (SPLIT(line, ' '))) AS word_count
FROM bucket.text;
```

Below is an explanation of the different functions:

- SPLIT(line, ' '): Splits the string line by spaces, returning an array of words.
- SIZE(array): Returns the size of the array, which in this case is the number of words in each line.
- SUM(): Adds up the total number of words across all rows in the table.

</details>

Depending on how you count the words, you should see around 31000 words.

We will now find the 10 most used words. This is somewhat complex because if you use the `SPLIT` function then it
returns an array, and you need to then use the [
`EXPLODE` function](https://tsaiprabhanj.medium.com/hive-explode-function-297b999e37dd).

**Task**: Find the 10 most used words in the Alice in Wonderland text.

<details>
<summary><strong>Hint:</strong> Top 10 most used words</summary>

```SQL
SELECT word, COUNT(*) AS count
FROM (
    SELECT EXPLODE(SPLIT(line, ' ')) AS word
    FROM bucket.text
    ) temp
GROUP BY word
ORDER BY count DESC
    LIMIT 10;
```

Each part of the SQL statement is explained below:

1. SPLIT(line, ' '): splits each line into words based on spaces, returning an array of words.
1. EXPLODE(): takes an array (in this case, the array of words from SPLIT) and turns each element into a separate row.
   This way, each word from the line is now treated as a row.
1. GROUP BY word: After exploding the array of words, we group by each unique word.
1. COUNT(*): This counts how many times each word appears in the dataset.
1. ORDER BY count DESC: Orders the words by their count in descending order, so the most frequent words appear first.
1. LIMIT 10: Limits the result to the 10 most frequent words.

</details>

The most used word is "the". This is not very surprising, both because it is a common word, but mostly because you
should already know this from exercises from previous lectures.

Just as an added bonus, you can actually get the name of files using `input__file__name`. For example, try executing the
following SQL statement:

```SQL
SELECT input__file__name AS path, SUM(SIZE (SPLIT(line, ' '))) AS word_count
FROM bucket.text
GROUP BY input__file__name;
```

Note that you need to use the `GROUP BY` clause in order to use `SELECT` on the path. This makes sense, because if you
don't do it, then the word count would just be of all files instead and have no knowledge of which files has what amount
of words.

You can also filter by the path:

```SQL
SELECT SUM(SIZE (SPLIT(line, ' '))) AS word_count
FROM bucket.text
WHERE input__file__name = 'hdfs://namenode:9000/<hdfs-path>/<file>';
```

The SQL statement above will only count the amount of words for files that match a specific path.

### Exercise 3 - Backblaze Hard Drive Data

[Backblaze](https://www.backblaze.com/) is a cloud backup and storage service. They have a lot of hard drives and
collect a lot of information about these drives in order to monitor health and figure out what drives are the most
reliable. We will be analyzing the Backblaze Hard Drive Data using Hive.

The data can be found [here](https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data). Download the drive
data for 2023 Q2. You can find this at the bottom of the page.

**Task**: Download drive data for 2023 Q2.

**Note**: The file is 860MB.

Once the file is downloaded, then unzip it and find the file called `2023-06-30.csv` and open it using a text editor.
The first line of the file contains information the names of each of the different columns in the CSV file. Look at the
first few rows, these are the ones we will be using for this exercise.

Create a new folder inside the HDFS and upload the `2023-06-30.csv` file to it.

**Task**: Upload drive data for 30/6/2023 into the new folder inside HDFS.

**Note**: It is important that the folder is empty. If it is not, then we will read the other files, which might result
in errors because the files are not of the same format.

We will now create a table for the Backblaze drive data.

**Task**: Create a table for the Backblaze drive data.

<details>
<summary><strong>Hint:</strong> Create CSV table</summary>

```SQL
CREATE
EXTERNAL TABLE IF NOT EXISTS bucket.backblaze (
  `date` STRING,
  serial_number STRING,
  model STRING,
  capacity_bytes STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/<path-to-folder>/'
TBLPROPERTIES (
  'skip.header.line.count'='1'
);
```

The format is CSV. We skip 1 header line because we don't want to include the header with column names as part of the
dataset.

</details>

Now that a table has been created, we will now query it.

**Task**: Get the first 100 rows of the CSV file.

**Hint:** See [exercise 2](./README.md#exercise-2---count-words-in-alice-in-wonderland-with-hive).

You should see 100 different disks and some information about them, such as the serial number, model and the capacity of
them. The dataset contains a lot of columns, such
as [S.M.A.R.T data](https://en.wikipedia.org/wiki/Self-Monitoring,_Analysis_and_Reporting_Technology) that contains
information about the disks.

We can now try to summarize the data. For example, what is the total count of each model of hard drive, and what is the
capacity of the hard drives in GB? Below is a task and a couple of questions that you could try to answer using Hive.

**Tasks:** Answer the following questions using Hive

- What is the total count of each model of hard drive?
- What is the capacity of the different hard drive models?
- What is the total capacity of each model of hard drive?
- What hard drive model is the most used?
- What hard drive model has the largest total capacity?

<details>
<summary><strong>Hint:</strong> Create SQL query</summary>

```SQL
SELECT model,
       FLOOR(CAST(capacity_bytes AS BIGINT) / POWER(10, 9))                   AS capacity_gigabytes,
       FLOOR(CAST(capacity_bytes AS BIGINT) / POWER(10, 9)) * COUNT(*) / 1000 AS total_capacity_terabytes,
       COUNT(*) AS count
FROM bucket.backblaze
WHERE input__file__name = 'hdfs://namenode:9000/<path-to-folder>/2023-06-30.csv'
GROUP BY model, capacity_bytes
ORDER BY count DESC;
```

</details>

**Tasks:** Compare the results to
the [blog post about the drive stats](https://www.backblaze.com/blog/backblaze-drive-stats-for-q2-2023/). For example,
the drive model `TOSHIBA MG07ACA14TA` is the most used with 38101 total drives. This is the same amount as what
Backblaze shows in their blog post.

### Exercise 4 - Compose a MongoDB cluster

The objective of this exercise is to interact with a NoSQL document-oriented database.
We will be working with MongoDB which is great for storing JSON like records with or without schemas and the database is
horizontal scalable.

**Note**: We will deploy the minimum configuration for this database in order to reduce the resource footprint.

This exercise is composed of three parts starting with a deployment of the MongoDB cluster. Then we would like to
revisit Kafka Connect similar to [Exercise 06](./../03/README.md#exercise-7---kafka-connect-and-hdfs) from lecture 3.
And finally we will look into querying JSON records in the database.

The [mongodb.yaml](./mongodb.yaml) contains a complete manifest to compose a MongoDB cluster. The manifest includes the
following resources:

```yml
- PersistentVolumeClaim: `mongodb-pvc`
- Services
    - `mongodb`
    - type: NodePort
    - port: 27017 <-> 27017
    - `mongo-express`
        - type: NodePort
        - port: 8081 <-> 8081
- Deployments
  - `mongodb`
  - `mongo-express`
```

**Task**: Familiarize yourself with the [mongodb.yaml](mongodb.yaml) manifest.
**Note**: Our example includes a simple authentication mechanism. The username and password have been hardcoded into
the [mongodb.yaml](mongodb.yaml) file. We do encourage you to apply a more sophisticated approach when you're
transferring into a production environment.

**Task**: Apply the [mongodb.yaml](mongodb.yaml) manifest to compose the MongoDB cluster.

<details>
  <summary><strong>Hint:</strong> Apply the deployment manifest</summary>

  ```bash
  kubectl apply -f mongodb.yaml
  ```

</details>

#### Exercise 4.1 - Interact with MongoDB

We will briefly introduce two approaches for interacting with MongoDB. One approach is the web-based interface called
`mongo-express` which is already included in the previously mentioned [mongodb.yaml](mongodb.yaml) manifest file.
The other approach is to install an extension for Visual Studio Code. Get further information on the extension
here: [MongoDB for VS Code](https://marketplace.visualstudio.com/items?itemName=mongodb.mongodb-vscode).

##### Web-based interface

The web-based `mongo-express` interface requires port-forwarding to access the site from your local host.

**Task**: Forward port `8081` from the `mongo-express` service to your local host.

<details>
<summary><strong>Hint:</strong> Get all the resources inside the `mongodb` namespace</summary>

```bash
kubectl port-forward svc/mongo-express 8081
```

</details>

**Task**: Open [127.0.0.1:8081](http://127.0.0.1:8081) and validate the hostname of the mongodb server. Does the server
name match the name of the `mongodb` Kubernetes pod?

**Note**: You will be prompted for a username and password. Please use `admin` and `pass` as log-in credentials
respectively.

**Task**: Explore the `mongodb`
documentation [here](https://www.mongodb.com/docs/manual/core/databases-and-collections/) and be confident in the
MongoDB terminology, e.g. document, collection, and databases.

**Task**: Explore the `mongo-express` documentation [here](https://github.com/mongo-express/mongo-express) and be
curious about the web-based interface [127.0.0.1:8081](http://127.0.0.1:8081).

##### MongoDB extension for Visual Studio Code

Another convenient approach for interacting with MongoDB is by using Visual Studio Code as a NoSQL editor. You can
enable this feature by installing
the [MongoDB for VS Code](https://marketplace.visualstudio.com/items?itemName=mongodb.mongodb-vscode) extension.

Similar to the web-based approach you need to set up port-forwarding to reach the `mongodb` pod from your local host.

**Task**: Forward port `27017` from the `mongodb` service to your local host.

<details>
<summary><strong>Hint:</strong> Get all the resources inside the `mongodb` namespace</summary>

```bash
kubectl port-forward svc/mongodb  27017
```

</details>

After the completion of the port-forwarding, you are able to insert the following connection string in the MongoDB for
VS Code extension: `mongodb://admin:password@127.0.0.1:27017`.

**Task**: Establish the connection to MongoDB using the extension.

**Task**: Explore the playgrounds tab inside the extension. Click "Create New Playground" and execute the new
playground.

**Task**: Explore the newly created database called `mongodbVSCodePlaygroundDB` and the inserted documents inside the
`sales` collections. You should find the identical documents inside the web
interface [here](http://127.0.0.1:8081/db/mongodbVSCodePlaygroundDB/sales).

#### Exercise 4.2 - MongoDB and Kafka connect

Multiple approaches for interfacing with MongoDB have been covered in the previous section. Now you need to fill
documents into the database before writing queries on the documents.

The objective of this exercise is to configure a Kafka Connect connector that uses the `INGESTION` topic as a source and
MongoDB as a sink. Therefore, the exercise assumes you have records inside the `INGESTION` topic.

**Task**: If the `INGESTION` topic is empty we recommend
revisiting [Exercise 03](./../03/README.md#exercise-4---produce-messages-to-kafka-using-python) from lecture 3 and
re-establish the Kafka produce to create new records.

**Task**: Configure a Kafka Connect connector to move records from Kafka to MongoDB.

**Hint:** This task can be solved with multiple approaches. Please start by revisiting the concept
in [Exercise 06](./../03/README.md#exercise-7---kafka-connect-and-hdfs) from lecture 3.

**Hint:** Then read the documentation
here: [Configure the Sink Connector](https://www.mongodb.com/docs/kafka-connector/current/tutorials/sink-connector/#configure-the-sink-connector).
The documentation suggests to post the configuration to the Kafka Connect REST API, which is similar to the approach
in [Exercise 06](./../03/README.md#exercise-7---kafka-connect-and-hdfs).

**NB:** Remember to set up port-forwarding for the Kafka Connect REST API.

<details>
<summary><strong>Hint:</strong> Post configuration</summary>

This example requires port-forwarding. Therefore, ensure `kubectl port-forward svc/kafka-connect 8083` is running in a
terminal on your local host.

Look into the configuration in the chunk below and execute the command in your terminal to create a Kafka Connect
connector:

```bash
curl -X POST \
http://127.0.0.1:8083/connectors \
-H 'Content-Type: application/json' \
-d '{
  "name": "mongodb-sink",
  "config": {
    "connection.password": "password",
    "connection.uri": "mongodb://admin:password@mongodb:27017",
    "connection.url": "mongodb://mongodb:27017",
    "connection.username": "admin",
    "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
    "database": "kafka",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "key.converter.schemas.enable": "true",
    "output.format.key": "json",
    "output.format.value": "json",
    "post.processor.chain": "com.mongodb.kafka.connect.sink.processor.DocumentIdAdder",
    "tasks.max": "4",
    "timeseries.timefield.auto.convert": "false",
    "topics": "INGESTION",
    "value.converter": "org.apache.kafka.connect.storage.StringConverter",
    "value.converter.schemas.enable": "true"
  }
}'
```

**Note:** If this does not work for you (Windows), then you can use this command (using Command Prompt NOT Powershell):

````bash
curl -X POST -H "Content-Type: application/json" -d @hints/configuration.json http://127.0.0.1:8083/connectors
````

</details>

**Task**: Validate that the connector is running. Please count the number of documents inside the `INGESTION`
collection. Does it match the number of records inside your `INGESTION` topic
in [redpanda](http://127.0.0.1:8080/topics/INGESTION#messages)?

<details>
<summary><strong>Hint:</strong> Count number of documents</summary>

You need to open a new playground in MongoDB for the VS Code extension to reproduce this hint.

The playground result of the chuck below will return the number of documents inside the `INGESTION` collection.

```js
use('kafka');
db.getCollection('INGESTION').countDocuments();
```

</details>

#### Exercise 4.3 - Query Documents in MongoBD

We are finally ready to start querying the documents inside MongoDB to answer important questions about the dataset.

You may find this documentation helpful to complete this exercise.

- [Query Documents](https://www.mongodb.com/docs/manual/tutorial/query-documents/#query-documents)
- [$regex](https://www.mongodb.com/docs/manual/reference/operator/query/regex/#-regex)

**Task**: Count the number of documents inside the `INGESTION` collection where the `sensor_id=6`.

<details>
<summary><strong>Hint:</strong> Count number of documents for sensor_id six</summary>

You need to open a new playground in MongoDB for the VS Code extension to reproduce this hint.

The playground result of the chuck below will return the number of documents inside the `INGESTION` collection.

```js
use('kafka');
db.getCollection('INGESTION').find({"payload": {$regex: /^{\"sensor_id\": 6/}}).count();
```

</details>

**Task**: Formalize a question to answer about the documents in MongoDB and create a proper query to answer this
question. Post the question and your solution in our Discord channel called "exercises".

### Exercise 5 - Highly available and scalable Redis cluster

We will now set up a highly available and scalable [Redis](https://redis.io/) cluster
using [Redis Cluster](https://redis.io/docs/management/scaling/)
and [Redis Sentinel](https://redis.io/docs/management/sentinel/). Redis is an open source, in-memory data structure
store (key values), used as a database, cache, and message broker. Redis cluster is horizontally scalable and uses
horizontal partitioning / sharding to store the different keys and values on different nodes.

The cluster will consist of 6 nodes, 3 are the primary nodes, and the 3 other ones are replica nodes. The replicas will
use [replication](https://redis.io/docs/management/replication/) and fail over strategies in order to ensure data is
available with minimal downtime. You can only write to primary nodes, no the replicas, but you can read from primary and
replicas. This can also be used make the primary nodes focus on only writing data, and then move all reads to the
replicas for maximum performance.

We will use the [Bitnami Redis Cluster helm chart](https://artifacthub.io/packages/helm/bitnami/redis-cluster). To
install the cluster, use the following command:

```bash
helm install redis oci://registry-1.docker.io/bitnamicharts/redis-cluster --version 11.0.4
```

The Bitnami chart will create a random password stored in a Kubernetes secret. To get the password, use the following
command:

MacOS / Linux

```bash
export REDIS_PASSWORD_BASE64=$(kubectl get secret redis-redis-cluster -o jsonpath="{.data.redis-password}")
echo $REDIS_PASSWORD_BASE64
```

Windows 

````text
$REDIS_PASSWORD_BASE64=$(kubectl get secret redis-redis-cluster -o jsonpath="{.data.redis-password}")
echo $REDIS_PASSWORD_BASE64
````

This will return the password in base64 format. You can decode it using the `base64 --decode` command on Unix (use PowerShell
if you are on Windows):

MacOS / Linux

```bash
export REDIS_PASSWORD=$(echo $REDIS_PASSWORD_BASE64 | base64 --decode)
echo $REDIS_PASSWORD
```

Windows

````bash
$REDIS_PASSWORD=$([System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($REDIS_PASSWORD_BASE64)))
echo $REDIS_PASSWORD
````

We will now create an interactive container that will be used to connect to the redis cluster. Run the following
command:

```bash
kubectl run redis-cluster-client --rm --tty -i --env REDIS_PASSWORD=$REDIS_PASSWORD --image docker.io/bitnamilegacy/redis-cluster:7.4.0-debian-12-r1 -- bash
```

You can then use the following command inside the interactive container to connect to the redis cluster using redis-cli:

```bash
redis-cli -c -h redis-redis-cluster -a $REDIS_PASSWORD
```

You are now connected to the redis cluster! Try to create a key using the [
`SET` command](https://redis.io/commands/set/). For example, `SET foo "bar"`. This will create / overwrite a key with
the name "foo" and give it the value "bar".

When you write commands to Redis you should see that it tells you what host it ran the command on. This is because the
keys are sharded across the redis nodes based on the key used. So if you write using the key `foo` and then get the key
again, it should redirect you to the same node.

Try to compare the IP address to the IPs of the pods inside the Kubernetes cluster. Use the command
`kubectl get pods -l app.kubernetes.io/instance=redis -o wide`. You should then be able to see what pod the value was
written to by comparing the IPs.

Because the redis cluster has replicas, then if a primary node fails, then a replica will be promoted. Try to delete the
pod that you just wrote the value to and then try to get the key again using the command: `GET foo`.

You should see that you are still able to get the key even though the primary node was killed. This is very cool 😎.

**Task**: What tactics does Redis Cluster + Redis Sentinel use?

## Step-by-step guide to clean up

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
    1. `kubectl delete pod redis-cluster-client`
    1. `helm uninstall redis`
    1. `kubectl delete pvc redis-data-redis-redis-cluster-0 \
      redis-data-redis-redis-cluster-1 \
      redis-data-redis-redis-cluster-2 \
      redis-data-redis-redis-cluster-3 \
      redis-data-redis-redis-cluster-4 \
      redis-data-redis-redis-cluster-5
      `
    1. `kubectl delete -f mongodb.yaml`
    1. `kubectl delete -f hive.yaml`
    1. `kubectl delete -f hive-metastore.yaml`
    1. `helm uninstall postgresql`
    1. `kubectl delete pvc data-postgresql-0`
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

You can get a list of the resources to verify that they are deleted.

- `kubectl get pods`
- `kubectl get services`
- `kubectl get deployments`
- `kubectl get configmap`
- `kubectl get pvc`
- `kubectl get all`
