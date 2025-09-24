# Setup infrastructure to instructors

The main idea is that the students only have to install the `kubectl` client. The instructors will setup the infrastructure and the students will only have to connect to the Kubernetes cluster though `<IP>:16443`.

## Allow incoming TCP traffic to port 16443

```bash
sudo iptables -A INPUT -p tcp --dport 16443 -s 10.X.0.0/12 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -s 10.x.0.0/12 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -s 10.152.183.1/12 -j ACCEPT
sudo iptables -A FORWARD -i cni0 -o cni0 -j ACCEPT
```

```bash
# flush all chains
sudo iptables -F
sudo iptables -t nat -F
sudo iptables -t mangle -F
# delete all chains
sudo iptables -X

sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT
sudo iptables -t nat -F
sudo iptables -t mangle -F
sudo iptables -F
sudo iptables -X
```

## Install Kubernetes distribution

We have chosen to use the [Microk8s](https://microk8s.io) distribution for this course. It is a lightweight distribution that is easy to install and manage. The distribution runs on bare metal and not containerized simulators like Minikube.

```bash
sudo snap install microk8s --classic
microk8s status --wait-ready
```


## Remove Kubernetes distribution

```bash
sudo snap remove microk8s --purge
```



### Addons

Addons enabled by default

````bash
dns
ha-cluster
helm
helm3
````

We will enable the following addons:

```bash
microk8s enable cert-manager
microk8s enable rbac
microk8s enable observability (Will also enable hostpath-storage and storage)
```

## Create workspace and service accounts for students

We will create a namespace, a service account, and a role for each namespace. The service account will be used together with a role binding to create a kubeconfig file for each of the students.

The above-mentioned steps are automated in the script [create-user.sh](create-user.sh). The file [create-users.sh](create-users.sh) parses the file [users.txt](users.txt) which includes a list of students for which we want to create access for.

### Step by step

1. Ensure the students are listed in the file `users.txt`
2. Run the following command to create the users on a Kubernetes node running the Microk8s distribution:

    ```bash
    ./create-users.sh "<IP>"
    ```

3. The script outputs the kubeconfig files for each student in the folder `~/tmp/<namespace>-kubeconfig.yaml`
4. Distribute the kubeconfig files to the students using SDU email. Inspiration is found here: [sent_msg_students.py](./share_kubeconfigs/sent_msg_students.py).

### Course project

The setup of the projects will be utilizing same namespace and service account approach as mentioned above. Therefore, update the content of the [users.txt](users.txt) file and follow the three first steps as above. Use the following file [sent_msg_groups.py](./share_kubeconfigs/sent_msg_groups.py) to distribute the kubeconfig to each group member.

## Share the kubeconfig file with the students

The kubeconfig file is the configuration file that the students will use to connect to the Kubernetes cluster. The file is generated in the previous step and should be shared with the students in a secure manner.

The current approach is to share the file through a secure messaging service directly to the students SDU email account. Please use a similar examples as this Python [sent_msg.py](./share_kubeconfigs/sent_msg.py) script to share the kubeconfig files.

## Add custom domain to Kubernetes API Certificates

1. Update the csr.conf.template in ´certs´ folder in the ´microk8s´ cluster

    ````bash
    sudo nano /var/snap/microk8s/current/certs/csr.conf.template
    ````

2. Add the new custom domain

    ````text
    ...

    [ alt_names ]
    DNS.1 = kubernetes
    DNS.2 = kubernetes.default
    DNS.3 = kubernetes.default.svc
    DNS.4 = kubernetes.default.svc.cluster
    DNS.5 = kubernetes.default.svc.cluster.local
    DNS.6 = CUSTOM-DOMAIN (Added)
    IP.1 = 127.0.0.1
    IP.2 = xxx.xxx.xxx.xxx
    IP.3 = SERVER_IP (Added, only if errors)
    #MOREIPS

    ...
    ````

3. Sign the CSR with the existing CA to generate a new server certificate

    ````bash
    sudo openssl x509 -req -in /var/snap/microk8s/current/certs/server.csr -CA /var/snap/microk8s/current/certs/ca.crt -CAkey /var/snap/microk8s/current/certs/ca.key -CAcreateserial -out /var/snap/microk8s/current/certs/server.crt -days 365 -extensions v3_ext -extfile /var/snap/microk8s/current/certs/csr.conf.template
    ````

4. Restart MicroK8s Services

    ````bash
    sudo microk8s stop
    sudo microk8s start
    ````

## Side-load container images

We will side-load the container images onto cluster in advanced in order to improve latency and limit network load. The current approach is described here. Execute the [side-load.sh](./images/side-load.sh) file or the [side-load.py](./images/side-load.py) file to load the images presented in the [images.txt](./images/images.txt) file into the cluster.

## Persist images

We will off-load the container images onto [gitlab.sdu.dk](https://gitlab.sdu.dk/jah/bigdatarepo/container_registry) to ensure reproducibility. Execute the [persist-images.py](./images/persist-images.py) file to pull, re-tag, and push the used images presented in the [images.txt](./images/images.txt) file.

## Observability

The Microk8s addon `observability` provides information about the Kubernetes cluster utilizing Prometheus to scape the K8's cluster.
To gain an overview of the cluster health and load, the addon comes with Grafana. The steps below shows how to gain access to the Grafana Dashboards.

1. Get the Grafana Stack credentials

    ````bash
    microk8s kubectl get secret -n observability kube-prom-stack-grafana -o jsonpath="{.data.admin-user}" | base64 --decode; echo
    microk8s kubectl get secret -n observability kube-prom-stack-grafana -o jsonpath="{.data.admin-password}" | base64 --decode; echo
    ````

2. Identify the Grafana Stack pod

    ````bash
    kubectl get pods -n observability
    ````

3. Port-forward the Grafana Stack pod

    ````bash
    kubectl port-forward -n observability kube-prom-stack-grafana-8dc65649-82k98 3000:3000
    ````

4. Enter the credentials

## Adjust allocated memory on root partition on host machine 

1. Check the currently used storage split across the different storage partitions 

````bash
df -h
````

**Output example:**

````text
Filesystem                         Size  Used Avail Use% Mounted on
tmpfs                              101G  6.5M  101G   1% /run
/dev/mapper/ubuntu--vg-ubuntu--lv   98G   76G   18G   4% /
tmpfs                              504G     0  504G   0% /dev/shm
tmpfs                              5.0M     0  5.0M   0% /run/lock
/dev/sda2                          2.0G  255M  1.6G  14% /boot
/dev/sda1                          1.1G  6.1M  1.1G   1% /boot/efi
````

**Note:** In this case the root partition is `/dev/mapper/ubuntu--vg-ubuntu--lv`

2. Check the total storage capacity for the host machine 

````bash
sudo vgdisplay
````

**Output example:**

````text
--- Volume group ---
  VG Name               ubuntu-vg
  System ID
  Format                lvm2
  Metadata Areas        1
  Metadata Sequence No  5
  VG Access             read/write
  VG Status             resizable
  MAX LV                0
  Cur LV                1
  Open LV               1
  Max PV                0
  Cur PV                1
  Act PV                1
  VG Size               6.98 TiB
  PE Size               4.00 MiB
  Total PE              1830606
  Alloc PE / Size       524288 / 2.00 TiB
  Free  PE / Size       1306318 / 4.98 TiB
  VG UUID               kbU86C-AtdF-bRrG-3GO3-qh4R-h4Ec-xF9x6y
````

3. Extend the Logical Volume

````text
lvextend -L <DESIRED SIZE> <FILE-SYSTEM-NAME>
````

**Example:**

````bash
sudo lvextend -L 1T /dev/ubuntu-vg/ubuntu-lv
````

4. Resize the Filesystem

````text
sudo resize2fs <FILE-SYSTEM-NAME>
````

**Example:**

````bash
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
````

5. Check the storage was updated for the storage partition

````bash
df -h
````

## Adjusting max pod limit

By default, a single node can only contain `110` pods. To increase the pod limit, follow the steps below:

1. Open the MicroK8s kubelet configuration file

    ````bash
    sudo nano /var/snap/microk8s/current/args/kubelet
    ````

2. Modify or add the `max-pods` setting to the desired amount e.g 1500

    ````bash
    --max-pods=1500
    ````

3. Save and close the file

4. Restart the microK8s cluster

    ````bash
    sudo microk8s.stop
    sudo microk8s.start
    ````

5. Verify the change

    ````bash
    kubectl describe node <your-node-name> 
    ````
