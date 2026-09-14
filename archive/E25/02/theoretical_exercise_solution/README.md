# Lecture 02 - HDFS and different file formats (Solution)

## Case Description

ReadBooks Inc. needs to store digital copies of all their books (+10M) containing the content of the books and appropriate metadata. They also want to enable analytics capabilities to present statistics of their inventories, such as word counts for specific book titles, overall word counts, etc.

### Solution Requirements

- The solution must store books with their names and entire contents in a proper file format.
- The solution must persist the data to a distributed filesystem.
- The solution should be able to store +10M books.
- The solution should have means to efficiently query word counts using various criteria.

### Demonstrate

- How to store book content and relevant metadata in distributed filesystem.
- How to read and write data in the chosen format.
- How to query data in the chosen format.

### Remember to

- Identify bottlenecks.
- Pick appropriate data format.
- Consider how scalability will be handled.
- Address data flow.
- Address how processed results will be accessed/presented.
- Present arguments for:
  - The chosen file format.
  - The chosen architecture.
  - The chosen technologies.

## Solution Proposal

### Architecture

```mermaid
flowchart TB
    
    subgraph Kubernetes
    subgraph HDFS
    namenode_1[NameNode 1]
    datanode_1[DataNode 1]
    datanode_2[DataNode 2]
    datanode_3[DataNode 3]

    namenode_1 e1@<--> datanode_1
    namenode_1 e2@<--> datanode_2
    namenode_1 e3@<--> datanode_3

    
    end
    client[client_i]
    


    client e4@<--> namenode_1


    
    e1@{ animation: fast }
    e2@{ animation: fast }
    e3@{ animation: fast }
    e4@{ animation: slow }
    
    end
```

**Deploy**

Read the instructions in the [HDFS service README](../../../services/hdfs/README.md) and deploy the HDFS cluster using the provided Kubernetes manifests.

```zsh
kubectl apply -f ../../../services/hdfs/configmap.yaml
kubectl apply -f ../../../services/hdfs/namenode.yaml
kubectl apply -f ../../../services/hdfs/datanodes.yaml
```

*Verify*

```zsh
kubectl port-forward svc/namenode 9870
```

```zsh
curl -s -XGET "http://localhost:9870/webhdfs/v1/?op=LISTSTATUS"
```

Deploy the client pod to interact with HDFS. I will use the provided [interactive.yaml](../../../services/interactive/interactive.yaml) manifest in the `services/interactive` folder.

```zsh
kubectl apply -f ../../../services/interactive/interactive.yaml
```

*Verify*

Attach to the pod using VS Code ([README.md](../../../services/interactive/README.md#attach-visual-studio-code-to-a-running-container)) or `kubectl exec -it pod/interactive-*-* -- /bin/bash`

```zsh
curl -s -XGET "http://namenode:9870/webhdfs/v1/?op=LISTSTATUS"
```

#### HDFS Folder Structure

```text
.
├── analytics
│   └── counting.parquet
├── books
│   ├── <UUDID>.avro
│   └── <UUDID>.avro
├── metadata.parquet
└── raw
    └── alice_in_wonderland.txt
```

**Create folders using CLI**

```zsh
hdfs dfs -fs hdfs://namenode:9000 -mkdir /raw /books /analytics
```

> You may need to run the following cmd:
> `export HADOOP_USER_NAME=root`.

**Download sample book**

[alice_in_wonderland.txt](https://storage.googleapis.com/kagglesdsdata/datasets/638254/1133676/alice_in_wonderland.txt?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20250910%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20250910T135842Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=3472fbd707af71a31678570f4d053c5e1b627833b761c96156db5a91b095737ed7f762e43e4403a493bf26fe912c43897123a9c0d7c67c3467bbfcea5ae01dc4befc9bc525aa613817b3c886def0e4ca96e20989a4a254b29bf2dd1f2fc1acfb1b4d0379216c2111b14b3f0560e3ecddcb8f8ba505cab6a033fbf182316022609edd057e2bef310bedd897e483f702c7e78c2a10c05ce444362368a168306da45b83f7e715a544aa1f6cfa138c7ae4b2af6f198b820c26daebbd6ac866bfb596e95a45b8294dff38e19dd5fda26dfde0b949a3bf6f32bbdd20175c8226c7a4f8f20821dc1bc3cbd919337093722e55065ff86a47a26a27acd01bebf42bb53fa0)

**Upload raw book to HDFS**

```zsh
hdfs dfs -fs hdfs://namenode:9000 -put alice_in_wonderland.txt /raw/
```

**Verify upload**

```zsh
hdfs dfs -fs hdfs://namenode:9000 -cat /raw/alice_in_wonderland.txt
```

### File formats

#### Avro Schema

/books/<UUID>.avro

```json
{
    "type": "record",
    "namespace": "default",
    "name": "BOOKS",
    "fields": [
        {"name": "id", "doc": "UUID of this book.", "type": "string"},
        {"name": "content", "doc": "Content of the bok.", "type": "string"},
    ],
}

```

#### Parquet Schemas

metadata.parquet

```python
{
    'id' : str, 
    'format': str,
    'path': str,
    'title': str,
    "author": str,
    'year': int,
    'language': str,
}
```

analytics/couting.parquet

```python
{
    'id' : str, 
    'word': str,
    'count': str,
}
```
