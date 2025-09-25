# Lecture 05 - Distributed Data Processing and Distributed Databases

Read case description here: [Case Description](../README.md)

## Proposed Architecture

### Step 1

- [] Show current state of architecture and current deployments.
![Alt text](images/step01.png)

## Step 2

- **"The solution must be able to store documents from a Kafka topic."**
- *"How to store documents from a Kafka topic."*

![Alt text](images/step02.png)

### Steps

- [] Deploy MongoDB and MongoDB Express
- [] Deploy a Kafka Connect MongoDB sink connector
- [] Demo that is works

### Resources

- [archive/E24/05/README.md -> Exercise 4 - Compose a MongoDB cluster](https://github.com/JakobHviidBDDST/BigDataCourseExercises/tree/main/archive/E24/05/README.md#exercise-4---compose-a-mongodb-cluster)

- ```zsh
  kubectl port-forward svc/mongo-express 8081
  ```

- [http://localhost:8081](http://localhost:8081)

- ```zsh
  kubectl port-forward svc/kafka-connect 8083
  ```

- ```zsh
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
      "tasks.max": "1",
      "timeseries.timefield.auto.convert": "false",
      "topics": "DOCS",
      "value.converter": "org.apache.kafka.connect.storage.StringConverter",
      "value.converter.schemas.enable": "true"
    }
  }'
  ```

## Step 3

- **"The solution must be able to cache the most recent records from each station for low-latency retrieval."**
- *"How to cache records for low-latency retrieval."*

![Alt text](images/step03.png)

### Steps

- [] Deploy Redis Cluster
- [] Deploy a Kafka Connect Redis sink connector
- [] Demo that is works

### Resources

- [archive/E24/05/README.md -> Exercise 5 - Highly available and scalable Redis cluster](https://github.com/JakobHviidBDDST/BigDataCourseExercises/tree/main/archive/E24/05/README.md#exercise-5---highly-available-and-scalable-redis-cluster)

- ```zsh
  helm install redis oci://registry-1.docker.io/bitnamicharts/redis --set architecture=standalone --set auth.enabled=false
  ```

- ```zsh
  kubectl port-forward svc/redis-master 6379
  ```

- ```zsh
  kubectl port-forward svc/kafka-connect 8083
  ```

- ```zsh
  curl -X POST \
  http://127.0.0.1:8083/connectors \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "redis-sink",
  "config": {
    "connector.class": "com.github.jcustenborder.kafka.connect.redis.RedisSinkConnector",
    "tasks.max": "1",
    "topics": "INGESTION",
    "redis.hosts": "redis-master:6379",
    "redis.type": "kv", 
    "redis.database": "0",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "value.converter": "org.apache.kafka.connect.converters.ByteArrayConverter",
    "value.converter.schemas.enable": "false"
  }
  }'
  ```


## Step 4

- **"The solution must be capable of analyzing text files stored long-term with SQL and Hive."**
- *"How to analyze text files in long-term storage and obtain specific word counts."*

![Alt text](images/step04.png)

### Steps

- [] Deploy Hive and Hive Metastore
- [] Create conenction to SQL editor
- [] Create table and point towards the file in HDFS
- [] Demo that is works

### Resources

- [archive/E24/05/README.md -> Exercise 1 - Hive](https://github.com/JakobHviidBDDST/BigDataCourseExercises/tree/main/archive/E24/05/README.md#exercise-1---hive)
- [archive/E24/05/README.md -> Exercise 2 - Count words in Alice in Wonderland with Hive](https://github.com/JakobHviidBDDST/BigDataCourseExercises/tree/main/archive/E24/05/README.md#exercise-2---count-words-in-alice-in-wonderland-with-hive)

```sql
SHOW TABLES;

CREATE
DATABASE IF NOT EXISTS warehouse
LOCATION 'hdfs://namenode:9000/hive/warehouse/';


CREATE TABLE IF NOT EXISTS warehouse.text_raw
(
    line STRING
) STORED AS TEXTFILE
LOCATION 'hdfs://namenode:9000/hive/raw';


SELECT * FROM warehouse.text_raw limit 100;

SELECT input__file__name AS path, SUM(SIZE(SPLIT(line, ' '))) AS word_count
FROM warehouse.text_raw
GROUP BY input__file__name;


SELECT word, COUNT(*) AS count
FROM (
    SELECT EXPLODE(SPLIT(line, ' ')) AS word
    FROM warehouse.text_raw
    ) temp
GROUP BY word
ORDER BY count DESC
    LIMIT 10;
```