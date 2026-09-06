# Lecture 05 - Distributed Data Processing and Distributed Databases

If your name is Tobias and you don't tell me you read this message during the exercise hours then you owe the instructors a beer.

## Exercises

Please open issues [here](https://github.com/jakobhviid/BigDataCourseExercises/issues) if you encounter unclear information or experience bugs in our examples!

Before you start working on the exercises you are strongly encouraged to clean up your Kubernetes cluster. The exercises will assume you use the MicroK8s cluster on the provided virtual machines and that the cluster is in a "clean" state.

### Exercise 1 - Set up Trino, Hive and Minio

[Trino](https://trino.io/) (formerly known as Presto) is a distributed SQL query engine for big data analytics. Trino is comparable to Apache Hive, but Trino can connect to many different data sources with [connectors](https://trino.io/docs/current/connector.html). Hive is also meant to run using YARN and it does not make sense to run YARN inside of Kubernetes. For that reason, the exercises will be about Trino.

You will be setting up a [Trino cluster](https://trino.io/docs/current/overview/concepts.html#cluster) and use the [Hive connector](https://trino.io/docs/current/connector/hive.html) to read files from an S3 bucket. An [Apache Hive metastore](https://cwiki.apache.org/confluence/display/hive/design#Design-Metastore) service is required in order to use the Hive connector. Hive metastore requires an SQL database to store data, so for this you will also set up a [PostgreSQL database](https://www.postgresql.org/).

You are also strongly encouraged to read [this](https://trino.io/Presto_SQL_on_Everything.pdf) paper about Trino, but it is not a requirement for the exercises.

#### Stackable operators

You will need the commons, secret, hive, and trino operators. We will create them inside the stackable namespace.

```text
kubectl create namespace stackable
helm repo add stackable-stable https://repo.stackable.tech/repository/helm-stable/
helm install -n stackable commons-operator stackable-stable/commons-operator --version 23.7.0
helm install -n stackable secret-operator stackable-stable/secret-operator --version 23.7.0 --set kubeletDir=/var/snap/microk8s/common/var/lib/kubelet
helm install -n stackable hive-operator stackable-stable/hive-operator --version 23.7.0
helm install -n stackable trino-operator stackable-stable/trino-operator --version 23.7.0
```

#### MinIO

Install MinIO

```text
helm install minio oci://registry-1.docker.io/bitnamicharts/minio --set service.type=NodePort --set auth.rootUser=admin --set auth.rootPassword=password
```

Create S3Connection that will be used by Hive metastore service to connect to MinIO.

Apply [s3connection.yaml](./s3connection.yaml).

#### Hive metastore service

The Hive metastore service will be deployed with PostgreSQL.

Deploy postgres database.

```text
helm install postgresql \
--version=12.1.5 \
--namespace default \
--set auth.username=hive \
--set auth.password=hive \
--set auth.database=hive \
--set primary.extendedConfiguration="password_encryption=md5" \
--repo https://charts.bitnami.com/bitnami postgresql
```

**Note:** You may have to delete the `\` and newlines so that it is one command.

Everything required to create the Hive metastore service is now ready. Apply the [hive.yaml](./hive.yaml) file.

#### Trino cluster

Apply the [trino.yaml](./trino.yaml) file. This file contains the TrinoCluster resource and TrinoCatalog resource. The [TrinoCatalog resource](https://docs.stackable.tech/home/stable/trino/concepts#_catalogs) is used to create an instance of a connector, in this case it is a Hive connector. Not a lot of connectors are supported by Stackable, but it will suffice for these exercises.

### Exercise 2 - Count words in Alice in Wonderland with Hive

We will now analyze the Alice in Wonderland text similarly to what we did in [lecture 2 exercse 6-8](../02/exercises.md#exercise-6---analyzing-file-and-saving-result-in-json-format-using-python) where we read a file from HDFS and counted words, and [lecture 4 exercise 3](../04/exercises.md#exercise-3---analyzing-files-using-spark-jobs) where we read a file from S3 and counted words using Spark. But this time we will analyze it using Trino.

#### Upload file to MinIO

Create a bucket inside the MinIO cluster and call it whatever you want.

**Task:** Create a bucket inside MinIO

Now upload the Alice in Wonderland file to a folder inside the bucket.

**Task:** Upload the Alice in Wonderland text to the bucket

**Note:** The file should be uploaded inside a folder, you can name the folder whatever you want you just need to remember it for later.

Everything is now prepared for us to use Trino.

#### Connect to Trino

A service has been created for the Trino cluster. Forward port 8443 of the Trino coordinator service.

**Task:** Forward Trino coordinator service

Open the forwarded service in your browser `https://localhost:8443`. Sign in to Trino using any username and no password.

**Task:** Open the Trino Web UI webpage and sign in

You should see that there is one active worker and no queries.

To connect to Trino we will use [DBeaver](https://dbeaver.io/). DBeaver is a cross-platform database tool that supports many different SQL databases.

**Task:** Download and install DBeaver

Now that DBeaver is installed we will now create a new database connection with the Trino cluster.

**Tasks:** Open DBeaver and create a new connection database connection using the following steps

1. Click on the "Database" tab and select "New Database Connection" from the dropdown
2. Search for Trino and select it, then click "Next" (and install drivers if prompted to)
3. Select "Connect by: URL" and enter the following url: `jdbc:trino://localhost:8443`
4. In the authentication box enter any username and no password
5. Click on the "Driver properties" tab, find the  `SSL` property and give it the value `true`
6. Create a user property by click on the blue button in the bottom left that says "Add user property" and name the property `SSLVerification` and give it the value `NONE`
7. Click on the "Test connection" button to make sure it works properly
8. If it works, then click on the "Finish" button

Now that a connection has been made to the Trino cluster we can then begin to write SQL statements. To write SQL statements then right-click on the connection you just made, then hover over the "SQL Editor", and then click on "Open SQL script".

**Task:** Create SQL editor

We can now begin to write SQL statements. First, we will make sure that the Hive connector has been set up.

**Task:** Show all catalogs

**Hint:** Enter the text `SHOW CATALOGS;`, then select it using your mouse and then press the keys `CTRL+ENTER` to execute the SQL statement.

You should see two catalogs, one called `hive` and another called `system`. You now know how to create and execute SQL statements using Trino. The name of the hive catalog comes from the name of the `TrinoCatalog` resource you applied to Kubernetes.

We will now [create a schema](https://trino.io/docs/current/sql/create-schema.html) inside the hive catalog. The schema is used to define where data is located, which will then be used by tables that are created with the schema.

**Task:** Create a schema

<details>
<summary><strong>Hint:</strong> Create schema</summary>

```SQL
CREATE SCHEMA IF NOT EXISTS hive.bucket
WITH (location = 's3a://<name of bucket>/');
```

Remember to enter the name of your bucket.
</details>

Now that a schema has been created, we will [create a table](https://trino.io/docs/current/sql/create-table.html) using the schema. The table needs to use the format `TextFile` and the location of the files that will be associated with the table. You can find more information about the formats supported by the Hive connector [here](https://trino.io/docs/current/connector/hive.html).

**Task:** Create a table using the schema you just made

<details>
<summary><strong>Hint:</strong> Create table</summary>

```SQL
CREATE TABLE hive.bucket.text (line VARCHAR)
WITH (
    format = 'TextFile',
    external_location = 's3a://<name of bucket>/<name of folder>/'
)
```

Remember to enter the name of your bucket and the name of the folder that Alice in Wonderland resides in.
</details>

We can now query the files inside the specified bucket and folder. Try to select a few lines from the table you just made.

**Task:** Run the following query `SELECT * FROM hive.bucket.text limit 100;`

You should see a list of the first 100 lines of the Alice in Wonderland text. Trino is very feature rich, please see the documentation about [SQL statement syntax]((https://trino.io/docs/current/sql.html)) and [functions and operators](https://trino.io/docs/current/functions.html) to get an idea of how to write SQL statements for Trino.

Similarly to the other exercises, we will now count the amount of words in the file, and after that we will figure out the 10 most used words.

To count words, you can split each line by spaces, then count the words for each line and then sum the counts.

**Task**: Count the total amount of "words" in the Alice in Wonderland text

<details>
<summary><strong>Hint:</strong> Count total words</summary>

```SQL
SELECT SUM(CARDINALITY(SPLIT(RTRIM(line), ' ')))
FROM hive.bucket.text;
```

Below is an explanation of the different functions:

- RTRIM removes trailing whitespaces
- SPLIT splits text by the specified text (in this case it is a space) and returns an array
- CARDINALITY returns the size of an array
- SUM returns the sum of all column values

</details>

Depending on how you count the words, you should see around 31000 words.

We will now find the 10 most used words. This is somewhat complex because if you use the `SPLIT` function then it returns an array, and you need to then use the [`UNNEST` function](https://trino.io/docs/current/sql/select.html#unnest).

**Task:** Find the 10 most used words in the Alice in Wonderland text

<details>
<summary><strong>Hint:</strong> Top 10 most used words</summary>

```SQL
SELECT DISTINCT word, COUNT(*) as count -- 4
FROM (
SELECT SPLIT(RTRIM(line), ' ') AS words -- 1
  FROM hive.bucket.text
)
CROSS JOIN UNNEST(words) AS T(word) -- 2
GROUP BY word -- 3
ORDER BY count DESC -- 5
LIMIT 10; -- 6
```

Each part of the SQL statement is explained below:

1. We first split the lines into words.
2. Then we unnest the words and cross join it, this results in all the elements inside the arrays to have their own row.
3. We then group by the word to find unique words.
4. We select the unique words, and the count of the words
5. Order the result by the count descending to have the most used words first
6. Limit to 10 to have get the 10 most used words.

</details>

The most used word is "the". This is not very surprising, both because it is a common word, but mostly because you should already know this from exercises from previous lectures.

Just as an added bonus, you can actually get the name of files using `"$path"`. For example, try executing the following SQL statement:

```SQL
SELECT "$path" AS path, SUM(CARDINALITY(SPLIT(RTRIM(line), ' ')))
FROM hive.bucket.text
GROUP BY "$path"
```

Note that you need to use the `GROUP BY` clause in order to use `SELECT` on the path. This makes sense, because if you don't do it, then the word count would just be of all files instead and have no knowledge of which files has what amount of words.

You can also filter by the path:

```SQL
SELECT SUM(CARDINALITY(SPLIT(RTRIM(line), ' ')))
FROM hive.bucket.text
WHERE "$path" = 's3a://<name of bucket>/<name of folder>/<name of file>'
```

The SQL statement above will only count the amount of words for files that match a specific path.

### Exercise 3 - Backblaze Hard Drive Data

[Backblaze](https://www.backblaze.com/) is a cloud backup and storage service. They have a lot of hard drives and collect a lot of information about these drives in order to monitor health and figure out what drives are the most reliable. We will be analyzing the Backblaze Hard Drive Data using Trino.

The data can be found [here](https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data). Download the drive data for 2023 Q2. You can find this at the bottom of the page.

**Task:** Download drive data for 2023 Q2

**Note:** The file is 860MB. This should hopefully not take too long...

Once the file is downloaded, then unzip it and find the file called `2023-06-30.csv` and open it using a text editor. The first line of the file contains information the names of each of the different columns in the CSV file. Look at the first few rows, these are the ones we will be using for this exercise.

Create a new folder inside the MinIO bucket you previously made and upload the `2023-06-30.csv` file to it.

**Task:** Upload drive data for 30/6/2023 into an empty folder inside a MinIO bucket

**Note:** It is important that the folder is empty. If it is not, then we will read the other files, which might result in errors because the files are not of the same format.

In Trino, all columns of a CSV file are treated as text. We can cast the text to other types, you can see all types [here](https://trino.io/docs/current/language/types.html).

We will now create a table for the Backblaze drive data.

**Task:** Create a table for the Backblaze drive data

<details>
<summary><strong>Hint:</strong> Create CSV table</summary>

```SQL
CREATE TABLE hive.bucket.backblaze (
  date VARCHAR,
  serial_number VARCHAR,
  model VARCHAR,
  capacity_bytes VARCHAR
)
WITH (
  skip_header_line_count = 1,
  format = 'CSV',
  external_location = 's3a://<name of bucket>/<name of folder>'
)
```

The format is CSV. We skip 1 header line because we don't want to include the header with column names as part of the dataset.

</details>

Now that a table has been created, we will now query it.

**Task:** Get the first 100 rows of the CSV file

**Hint:** See [exercise 2](./exercises.md#exercise-2---count-words-in-alice-in-wonderland-with-hive)

You should see 100 different disks and some information about them, such as the serial number, model and the capacity of them. The dataset contains a lot of columns, such as [S.M.A.R.T data](https://en.wikipedia.org/wiki/Self-Monitoring,_Analysis_and_Reporting_Technology) that contains information about the disks.

We can now try to summarize the data. For example, what is the total count of each model of hard drive, and what is the capacity of the hard drives in GB? Below is a task and a couple of questions that you could try to answer using Trino.

**Tasks:** Answer the following questions using Trino

- What is the total count of each model of hard drive?
- What is the capacity of the different hard drive models?
- What is the total capacity of each model of hard drive?
- What hard drive model is the most used?
- What hard drive model has the largest total capacity?

<details>
<summary><strong>Hint:</strong> Create SQL query</summary>

```SQL
SELECT
  model,
  FLOOR(CAST(capacity_bytes as BIGINT) / POWER(10, 9)) AS capacity_gigabytes,
  FLOOR(CAST(capacity_bytes as BIGINT) / POWER(10, 9)) * COUNT(*) AS total_capacity_terabytes,
  COUNT(*) AS count
FROM hive.bucket.backblaze
WHERE "$path" = 's3a://<name of bucket>/<name of folder>/2023-06-30.csv'
GROUP BY model,capacity_bytes
ORDER BY count DESC;
```
</details>

**Tasks:** Compare the results to the [blog post about the drive stats](https://www.backblaze.com/blog/backblaze-drive-stats-for-q2-2023/). For example, the drive model `TOSHIBA MG07ACA14TA` is the most used with 38101 total drives. This is the same amount as what Backblaze shows in their blog post.


### Exercise 4 - Compose a MongoDB cluster
The objective of this exercise is to interact with a NoSQL document-oriented database. 
We will be working with MongoDB which is great for storing JSON like records with or without schemas and the database is horizontal scalable.

**Note:** We will deploying the minimum configuration for this database in order to reduce the recoruse footprint. 

This exercise is composed of three parts starting wiht a deployment of the MongoDB cluster. Then we would like to revist Kafka Connect similar to [Exercise 06](./../03/exercises.md#exercise-6---kafka-connect-and-hdfs) from lecture 3. And finally we will look into querying JSON records in the database.


We recommand to create a isolated namespace for the following MongoDB services.

**Task:** Create a namepsace in Kubernetes called `mongodb`.
<details>
  <summary><strong>Hint:</strong> Create namespace</summary>

  ```
  kubectl create namespace mongodb 
  ```
  
</details>



The [mongodb.yaml](mongodb.yaml) contains a complete manifest to compose a MongoDB cluster. The manifest includes the following recources:
- PersistentVolumeClaim: `mongodb-pvc`
- Services
  - `mongodb`
    - type: NodePort
    - port: 27017 <-> 27017
  - `mongo-express`
    - type: NodePort
    - port: 8084 <-> 8084
- Deployments
  - `mongodb`
  - `mongo-express`

**Task:** Familize yourself with the [mongodb.yaml](mongodb.yaml) manifest.
**Note:** Our example includes a simple authentication mecanishm. The username and password have been hardcoded into the [mongodb.yaml](mongodb.yaml) file. We do encurge you to apply a more sufisticated approach when you transfering into a production environment. 


**Task:** Apply the [mongodb.yaml](mongodb.yaml) manifest to compose the MongoDB cluster.
<details>
  <summary><strong>Hint:</strong> Apply the deployment manifest</summary>

  ```
  kubectl apply -f mongodb.yaml
  ```

</details>



**Task:** Validate your deployment of MongoDB.

<details>
  <summary><strong>Hint:</strong> Get all the resources inside the `mongodb` namespace</summary>

  One approach for getting the current state of the deployed resources is by using the command below:


  ```
  kubectl get all -n mongodb  
  ```
  You should expect a similar output like the chunk below:

  ```
  NAME                               READY   STATUS    RESTARTS   AGE
  pod/mongodb-f585b897b-f7bn6        1/1     Running   0          7m31s
  pod/mongo-express-f896d549-5gbz7   1/1     Running   0          2m51s

  NAME                               TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)           AGE
  service/mongodb                    NodePort   10.152.183.106   <none>        27017:32346/TCP   7m32s
  service/mongo-express              NodePort   10.152.183.163   <none>        8084:31280/TCP    7m32s

  NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
  deployment.apps/mongodb            1/1     1            1           7m32s
  deployment.apps/mongo-express      1/1     1            1           7m31s

  NAME                                     DESIRED   CURRENT   READY   AGE
  replicaset.apps/mongodb-f585b897b        1         1         1       7m31s
  replicaset.apps/mongo-express-f896d549   1         1         1       2m51s
  ```

</details>


#### Exercise 4.1 - Interact with MongoDB

We will briefly introduce two approaches for interacting with MongoDB. One approach is the web-based interface called `mongo-express` which is already included in the previously mentioned [mongodb.yaml](mongodb.yaml) manifest file. 
The other approach is to install an extension for Visual Studio Code. Get further information on the extension here: [MongoDB for VS Code](https://marketplace.visualstudio.com/items?itemName=mongodb.mongodb-vscode).


##### Web-based interface
The web-based `mongo-express` interface requires port-forwarding to access the site from your local host.

**Task:** Forward port `8084` from the `mongo-express` service to your local host.
<details>
  <summary><strong>Hint:</strong> Get all the resources inside the `mongodb` namespace</summary>

  ```
  kubectl port-forward svc/mongo-express  8084:8084 -n mongodb
  ```
</details>


**Task:** Open [127.0.0.1:8084](http://127.0.0.1:8084) and validate the hostname of the mongodb server. Does the server name match the name of the `mongodb` Kubernetes pod?

**Note:** You will be prompted for a username and password. Please use `admin` and `pass` as log-in credentials respectively.

**Task:** Explore the `mongodb` documentation [here](https://www.mongodb.com/docs/manual/core/databases-and-collections/) and be confident in the MongoDB terminology, e.g. document, collection, and databases.

**Task:** Explore the `mongo-express` documentation [here](https://github.com/mongo-express/mongo-express) and be curious about the web-based interface [127.0.0.1:8084](http://127.0.0.1:8084).


##### MongoDB extension for Visual Studio Code

Another convenient approach for interacting with MongoDB is by using Visual Studio Code as a NoSQL editor. You can enable this feature by installing the [MongoDB for VS Code](https://marketplace.visualstudio.com/items?itemName=mongodb.mongodb-vscode) extension. 

Similar to the web-based approach you need to set up port-forwarding to reach the `mongodb` pod from your local host.

**Task:** Forward port `27017` from the `mongodb` service to your local host.
<details>
  <summary><strong>Hint:</strong> Get all the resources inside the `mongodb` namespace</summary>

  ```
  kubectl port-forward svc/mongodb  27017:27017 -n mongodb 
  ```
</details>

After the completion of the port-forwarding, you are able to insert the following connection string in the MongoDB for VS Code extension: `mongodb://admin:password@127.0.0.1:27017`

**Task:** Establish the connection to MongoDB using the extension.

**Task:** Explore the playgrounds tab inside the extension. Click "Create New Playground" and execute the new playground.

**Task:** Explore the newly created database called `mongodbVSCodePlaygroundDB` and the inserted documents inside the `sales` collections. You should find the identical documents inside the web interface [here](http://127.0.0.1:8084/db/mongodbVSCodePlaygroundDB/sales).


#### Exercise 4.2 - MongoDB and Kafka connect
Multiple approaches for interfacing with MongoDB have been covered in the previous section. Now you need to fill documents into the database before writing queries on the documents.

The objective of this exercise is to configure a Kafka Connect connector that uses the `INGESTION` topic as a source and MongoDB as a sink. Therefore the exercise assumes you have records inside the `INGESTION` topic. 

**Task:** If the `INGESTION` topic is empty we recommend revisiting [Exercise 03](./../03/exercises.md#exercise-3---produce-messages-to-kafka-using-python) from lecture 3 and re-establish the Kafka produce to create new records.

**Task:** Configure a Kafka Connect connector to move records from Kafka to MongoDB.

**Hint:** This task can be solved with multiple approaches. Please start by revisiting the concept in [Exercise 06](./../03/exercises.md#exercise-6---kafka-connect-and-hdfs) from lecture 3.

**Hint:** Then read the documentation here: [Configure the Sink Connector](https://www.mongodb.com/docs/kafka-connector/current/tutorials/sink-connector/#configure-the-sink-connector). The documentation suggests to post the configuration to the Kafka Connect REST API, which is similar to the approach in [Exercise 06](./../03/exercises.md#exercise-6---kafka-connect-and-hdfs).

**NB:** Remember to setup port-forwarding for the Kafka Connect REST API.

<details>
  <summary><strong>Hint:</strong> Post configuration</summary>

    This example requires port-forwarding. Therefore ensure `kubectl port-forward svc/kafka-connect 8083:8083 -n kafka` is running in a terminal on your local host.

    Look into the configuration in the chunk below and execute the command in your terminal to create a Kafka Connect connector:

```sh
curl -X POST \
http://127.0.0.1:8083/connectors \
-H 'Content-Type: application/json' \
-d '{
    "name": "mongodb-sink",
    "config": {
        "connection.password": "password",
        "connection.uri": "mongodb://admin:password@mongodb.mongodb:27017",
        "connection.url": "mongodb://mongodb.mongodb:27017",
        "connection.username": "admin",
        "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
        "database": "kafka",
        "key.converter": "org.apache.kafka.connect.storage.StringConverter",
        "key.converter.schemas.enable": "true",
        "name": "mongodb-sink-connector-cdfs",
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
</details>


**Task:** Validate that the connector is running. Please count the number of documents inside the `INGESTION` collection. Does it match the number of records inside your `INGESTION` topic in [redpanda](http://127.0.0.1:8080/topics/INGESTION#messages)?


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

**Task:** Count the number of documents inside the `INGESTION` collection where the `sensor_id=6`.

<details>
  <summary><strong>Hint:</strong> Count number of documents for sensor_id six </summary>
  You need to open a new playground in MongoDB for the VS Code extension to reproduce this hint.

  The playground result of the chuck below will return the number of documents inside the `INGESTION` collection.

  ```js
  use('kafka');
  db.getCollection('INGESTION').find({ "payload": { $regex: /^{\"sensor_id\": 6/ } }).count();
  ```
</details>

**Task:** Formulize a question to answer about the documents in MongoDB and create a proper query to answer this question. Post the question and your solution in our Discord channel called "exercises".

### Exercise 5 - Highly available and scalable Redis cluster

We will now set up a highly available and scalable [Redis](https://redis.io/) cluster using [Redis Cluster](https://redis.io/docs/management/scaling/) and [Redis Sentinel](https://redis.io/docs/management/sentinel/). Redis is an open source, in-memory data structure store (key values), used as a database, cache, and message broker. Redis cluster is horizontally scalable and uses horizontal partitioning / sharding to store the different keys and values on different nodes.

The cluster will consist of 6 nodes, 3 are the primary nodes, and the 3 other ones are replica nodes. The replicas will use [replication](https://redis.io/docs/management/replication/) and failover strategies in order to ensure data is available with minimal downtime. You can only write to primary nodes, no the replicas, but you can read from primary and replicas. This can also be used make the primary nodes focus on only writing data, and then move all reads to the replicas for maximum performance.

We will use the [Bitnami Redis Cluster helm chart](https://artifacthub.io/packages/helm/bitnami/redis-cluster). To install the cluster, use the following command:

```text
helm install redis oci://registry-1.docker.io/bitnamicharts/redis-cluster
```

The Bitnami chart will create a random password stored in a Kubernetes secret. To get the password, use the following command:

```text
kubectl get secret redis-redis-cluster -o jsonpath="{.data.redis-password}"
```

This will return the password in base64 format. You can decode it using the `base64 --decode` command on Unix (use WSL if you are on Windows):

```text
echo "<base64 password>" | base64 --decode
```

We will now create an interactive container that will be used to connect to the redis cluster. Run the following command:

```text
kubectl run redis-cluster-client --rm --tty -i --env REDIS_PASSWORD=<password> --image docker.io/bitnamilegacy/redis-cluster:7.2.1-debian-11-r0 -- bash
```

You can then use the following command inside of the interactive container to connect to the redis cluster using redis-cli:

```text
redis-cli -c -h redis-redis-cluster -a $REDIS_PASSWORD
```

You are now connected to the redis cluster! Try to create a key using the [`SET` command](https://redis.io/commands/set/). For example, `SET foo "bar"`. This will create / overwrite a key with the name "foo" and give it the value "bar".

When you write commands to Redis you should see that it tells you what host it ran the command on. This is because the keys are sharded accross the redis nodes based on the key used. So if you write using the key `foo` and then get the key again, it should redirect you to the same node.

Try to compare the IP address to the IPs of the pods inside the Kubernetes cluster. Use the command `kubectl get pods -l app.kubernetes.io/instance=redis -o wide`. You should then be able to see what pod the value was written to by comparing the IPs.

Because the redis cluster has replicas, then if a primary node fails, then a replica will be promoted. Try to delete the pod that you just wrote the value to and then try to get the key again using the command: `GET foo`.

You should see that you are still able to get the key even though the primary node was killed. This is very cool 😎.

**Task:** What tactics does Redis Cluster + Redis Sentinel use?
