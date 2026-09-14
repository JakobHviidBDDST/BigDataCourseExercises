# HDFS

We will be using the following Docker images for the HDFS cluster:

- [bde2020/hadoop-namenode:2.0.0-hadoop3.2.1-java8](https://hub.docker.com/r/bde2020/hadoop-namenode)
- [bde2020/hadoop-datanode:2.0.0-hadoop3.2.1-java8](https://hub.docker.com/r/bde2020/hadoop-datanode)

## Installation

The following steps will guide you through the installation of an HDFS cluster on Kubernetes.
Before proceeding, make sure you have a Kubernetes cluster running and `kubectl` configured to use the cluster and familiarize yourself with the following resoruce files:

- [configmap.yaml](./configmap.yaml)
- [datanodes.yaml](./datanodes.yaml)
- [namenode.yaml](./namenode.yaml)

Once ready, apply the following commands to deploy the HDFS cluster in the following order

1. Deploy the configmap

````bash
kubectl apply -f configmap.yaml
````

2. Ensure it's deployed

````bash
kubectl get configmap hadoop-config
````

3. Deploy the namenode.yaml

````bash
kubectl apply -f namenode.yaml
````

4. Ensure the pod is created successfully

````bash
kubectl get pod -w
kubectl describe pod namenode-<ID>
kubectl logs namenode-<ID>
````

5. Deploy the datanodes.yaml

````bash
kubectl apply -f datanodes.yaml
````

6. Ensure that 3 datanode pods are created successfully

````bash
kubectl get pod -w 
````

### Verify HDFS works

Create a connection to namenode pod using port-forwarding as below:

```bash
kubectl port-forward svc/namenode 9870:9870
```

We expect the HDFS cluster to be empty once installed. The following command shows the root directory in HDFS by the namenode pod.

```bash
curl -s -XGET "http://localhost:9870/webhdfs/v1/?op=LISTSTATUS"
```

It should return the following:
```json
{
    "FileStatuses": {
        "FileStatus": [

        ]
    }
}
```

## Cleanup

To remove the HDFS cluster, run the following commands:

```bash
kubectl delete -f datanodes.yaml
kubectl delete -f namenode.yaml
kubectl delete -f configmap.yaml
```
