# Lecture 01 - Kubernetes fundamentals

## Introduction to the instructors

### Oliver Feldborg Hansen

![Oliver Feldborg Hansen](https://media.licdn.com/dms/image/v2/D4E03AQFmQrvFqB4u5A/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1713376210091?e=1758153600&v=beta&t=pvpHb_XR4s-evlX41LPsDMOLJla6lRCDZjZHDGrtMhc)

- 9th semester Software Engineering student
- Industry for 1 year
    - Student Worker in DevOps ~ Mobile Industrial Robots
- Studying Master of Science in Software Engineering ~University of Southern Denmark
- Bachelor in Engineering in Software Engineering ~University of Southern Denmark
- LinkedIn ~ [linkedin.com/in/oliverfhansen](https://www.linkedin.com/in/oliverfhansen/)

### Anders Launer Bæk-Petersen

![Anders Launer Bæk-Petersen](https://avatars.githubusercontent.com/u/28479232?v=4)

- PhD Fellow ~ SDU Software Engineering
    - Understanding the Reliability of Machine Learning
      Systems from a Software Engineering Perspective
- PhD Fellow ~ SDU Center for Energy Informatics
    - Transferable AI Model Development Framework for Smart Energy Systems
- Industry for 4,5 years
    - Machine Learning Engineer ~ Energinet
    - Data Scientist ~Esoft R&D
    - Research Assistant ~Technical University of Denmark
- Master of Science in Mathematical Modelling and Computation ~Technical University of Denmark
- Bachelor of Science in Robot Systems ~University of Southern Denmark
- LinkedIn ~ [linkedin.com/in/anderslaunerbaek](https://www.linkedin.com/in/anderslaunerbaek/)

## Exercise lectures

The format of the exercise lectures is as follows:

- Two modules of 45 minutes each per week.
- Each module will contain a case, based on the themes of the lecture, where you must pick and connect the appropriate technologies to solve the case, and then apply said technologies.
- To help familiarize yourselves with the technologies, please refer to the archived exercises for [E24](https://github.com/JakobHviidBDDST/BigDataCourseExercises/tree/main/archive/E24), as these contain guides and usage examples for the technologies.
- A proposed solution for the case will be published before the next lecture. 
- The first half of the first module will be used for recap and solution sharing from the previous exercises. 
The remainder of the first module and the second module will be used to work with the exercises for the current week.
- The exercises will be provided in `README.md` file in the respective lecture folder.

Please open issues [here](https://github.com/jakobhviid/BigDataCourseExercises/issues) if you encounter unclear information or experience bugs in our examples!

## Subject and objective for this exercises

The exercises for the first lecture are to introduce and refresh the necessary components and terminology of Kubernetes. This will be the only purely hands-on exercise, without a case.
 
The below-mentioned material has been sourced
from [https://kubernetes.io/docs/tutorials/kubernetes-basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
and familiarizing with this content will be sufficient for progressing along the exercises.

The objective of this lecture is to provide the foundation for future exercise sessions and for the semester project.

NOTE: If you participated in Enigma's *"Kubernetes: Getting started with Enigma"* course, you should be able to skip directly to [Exercise 1](#exercise-1---kubernetes-setup), set up your kubeconfigs and skip directly to [Exercise 5](#exercise-5---deploy-the-application-using-helm) to get a quick overview of Helm.

## Brief introduction to Kubernetes

Kubernetes was one of the answers to moving from pure virtualization towards infrastructure as a service and being the
convenient abstraction for decoupling applications and the underlying hardware.

We recommend watching the
documentary [Kubernetes: The Documentary [PART 1]](https://youtu.be/BE77h7dmoQU?si=qohxiWDd52EpPoHP)
and [Kubernetes: The Documentary [PART 2]](https://youtu.be/318elIq37PE?si=_Pjgstj7w_9OlsUf) to get context and history
of the preliminary enablers for Kubernetes.

### [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)

Kubernetes is a cluster orchestration system that enables the deployment of containerised applications on virtualized
hardware or bare metal hardware.

> Kubernetes is a production-grade, open-source platform that orchestrates the placement (scheduling) and execution of
> application containers within and across computer clusters.
*[kubernetes.io - Cluster Diagram. (Accessed: 04 September 2023)](https://kubernetes.io/docs/tutorials/kubernetes-basics/create-cluster/cluster-intro/)*

The diagram below illustrates the core components of a Kubernetes cluster. The Kubernetes cluster consists of one or
multiple nodes that execute the application processes and control plane resource that coordinates the application
activities across the nodes.

![Kubernetes Cluster](https://d33wubrfki0l68.cloudfront.net/283cc20bb49089cb2ca54d51b4ac27720c1a7902/34424/docs/tutorials/kubernetes-basics/public/images/module_01_cluster.svg)
*Image
from [kubernetes.io - Cluster Diagram. (Accessed: 04 September 2023)](https://d33wubrfki0l68.cloudfront.net/283cc20bb49089cb2ca54d51b4ac27720c1a7902/34424/docs/tutorials/kubernetes-basics/public/images/module_01_cluster.svg)*

### [Using kubectl to Create a Deployment](https://kubernetes.io/docs/tutorials/kubernetes-basics/deploy-app/deploy-intro/)

A Kubernetes deployment is the recipe for running your application. The control plane will constantly monitor the state
of the application and provide self-healing actions if the current application instance is unresponsive.

![ Deploying your first app on Kubernetes](https://d33wubrfki0l68.cloudfront.net/8700a7f5f0008913aa6c25a1b26c08461e4947c7/cfc2c/docs/tutorials/kubernetes-basics/public/images/module_02_first_app.svg)
*Image
from [kubernetes.io - Deploying your first app on Kubernetes. (Accessed: 04 September 2023)](https://d33wubrfki0l68.cloudfront.net/8700a7f5f0008913aa6c25a1b26c08461e4947c7/cfc2c/docs/tutorials/kubernetes-basics/public/images/module_02_first_app.svg)*

`kubectl` is the CLI for Kubernetes and the CLI can be used to create a deployment of containerized applications or
manage already deployed applications, fetch logs from the application, and much more.

### [Viewing Pods and Nodes](https://kubernetes.io/docs/tutorials/kubernetes-basics/explore/explore-intro/)

#### Pods

A Kubernetes Pod is an abstraction generated by a Kubernetes deployment. The Pod behaves as a logical host and is
hosting one or multiple containerized applications as illustrated in the figure below.

![Pods overview](https://d33wubrfki0l68.cloudfront.net/fe03f68d8ede9815184852ca2a4fd30325e5d15a/98064/docs/tutorials/kubernetes-basics/public/images/module_03_pods.svg)
*Image
from [kubernetes.io - Pods overview. (Accessed: 04 September 2023)](https://d33wubrfki0l68.cloudfront.net/fe03f68d8ede9815184852ca2a4fd30325e5d15a/98064/docs/tutorials/kubernetes-basics/public/images/module_03_pods.svg)*

#### Nodes

A Kubernetes node can be described as a worker within the Kubernetes cluster. The node is managed by the control plane
and can host several different Pods as illustrated in the figure below.
![Node overview](https://d33wubrfki0l68.cloudfront.net/5cb72d407cbe2755e581b6de757e0d81760d5b86/a9df9/docs/tutorials/kubernetes-basics/public/images/module_03_nodes.svg)
*Image
from [kubernetes.io - Node overview. (Accessed: 04 September 2023)](https://d33wubrfki0l68.cloudfront.net/5cb72d407cbe2755e581b6de757e0d81760d5b86/a9df9/docs/tutorials/kubernetes-basics/public/images/module_03_nodes.svg)*

### [Using a Service to Expose Your App](https://kubernetes.io/docs/tutorials/kubernetes-basics/expose/expose-intro/)

Each Kubernetes Pod has a different IP address as seen in the figure above. These IP addresses are local to the cluster
and not accessible from outside the cluster. For some applications, we need to have an abstraction, which maps external
traffic to the deployment (Pod) of interest. The Pods have a lifecycle and their IP address change due to rescheduling
to another node.

![Services and Labels](https://d33wubrfki0l68.cloudfront.net/7a13fe12acc9ea0728460c482c67e0eb31ff5303/2c8a7/docs/tutorials/kubernetes-basics/public/images/module_04_labels.svg)
*Image
from [kubernetes.io - Services and Labels. (Accessed: 04 September 2023)](https://d33wubrfki0l68.cloudfront.net/7a13fe12acc9ea0728460c482c67e0eb31ff5303/2c8a7/docs/tutorials/kubernetes-basics/public/images/module_04_labels.svg)*

A Kubernetes Service is the abstraction we need to provide a loosely coupling Pods and external traffic. There are
multiple types of Services:

- ClusterIP
- NodePort
- LoadBalancer
- ExternalName

Get full definitions
here: [Overview of Kubernetes Services](https://kubernetes.io/docs/tutorials/kubernetes-basics/expose/expose-intro/)

> A Kubernetes Service is an abstraction layer which defines a logical set of Pods and enables external traffic
> exposure, load balancing and service discovery for those Pods.
*[kubernetes.io - Using a Service to Expose Your App. (Accessed: 04 September 2023)](https://kubernetes.io/docs/tutorials/kubernetes-basics/expose/expose-intro/)*

## Exercises

### Exercise 1 - Kubernetes setup

#### The kubectl CLI

The CLI tool used to communicate with a Kubernetes cluster from your localhost is called "kubectl". It is used though
the terminal like `kubectl <command> <flags>`.
You read more about the CLI and how to install it
here: [install kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl).

#### The kubeconfig file

You will receive a kubeconfig file before starting on lecture 1. Your personal config file will be shared by email and
is needed to access the Kubernetes cluster.

The kubeconfig file is located in the `~/.kube` directory in your home directory. The file is named `config` and is used
by default when running the `kubectl` command.
The kubeconfig file contains the necessary information to connect to the cluster and authenticate with it. The file is
used by the `kubectl` CLI to connect to the cluster.

**Task**: Please update the `~/.kube/config` file with the provided content.

**Note**: You are able to specify the kubeconfig file to use by using the `--kubeconfig` flag.

#### Wrap up

> All the following exercises assume you have access to the Kubernetes cluster and the `kubectl` CLI installed on your
> local host.

### Exercise 2 - Deploy "Hello World" application

The first thing you will be doing with the Kubernetes cluster is to deploy a hello world application. The application
can be found on GitHub [paulbouwer/hello-kubernetes](https://github.com/paulbouwer/hello-kubernetes). A yaml file to
deploy the application can be found [here](./hello-kubernetes.yaml).

The yaml file contains two resources, a deployment and a service. Deployments are used to create pods, and services are
used to route traffic to the pods using label selectors. A major part of Kubernetes is the use of labels and selectors.
Labels are key-value pairs that can be used for filtering.

Inspect the yaml manifest and understand the different parts of it:

- Identify the two resources.
- Identify the labels and selectors. How are they used?
- Try to understand how the environment variables are added to the pods.

Now that you have looked through the yaml you may have figured out the following:

- The deployment creates 3 pods.
- The pods have 3 environment variables that use a `fieldRef`.
- The container listens on port 8080.
- The service listens for traffic on port 8080 and routes it to port 8080 inside the pod.

The `fieldRef` inside the environment variables is used to reference a field of the pod and use the value of it as an
environment variable.

- `metadata.namespace` is used to reference the namespace that the pod is inside. When no namespace is provided for a
  resource, then the "default" namespace is used.
- `metadata.name` is used to reference the name of the pod. The name is automatically generated using the name of the
  replica set + a random string for each pod. The name of the replicaset comes from the name of the deployment + a hash
  to uniquely identify the revision.
- `spec.nodeName` is used to reference the name of the node that the pod is scheduled to run on.

Now that you understand the yaml file, run the command `kubectl apply -f hello-kubernetes.yaml` to apply the resources
to the Kubernetes cluster. You can then use `kubectl get pods` to get a list of the pods and `kubectl get service` to
get a list of the services.

### Exercise 3 - Connecting to the application

Now that you have deployed the application the next step is to try and connect to it. The application is an HTTP server
that listens for requests on port 8080. To connect to the application, we should do it through the service.

Connecting to a service can be done in different ways. The simplest way to connect to a service inside the cluster and
to your localhost is by running the `kubectl port-forward` command.

#### Use port forwarding

To use the `kubectl port-forward` command, run the following command
`kubectl port-forward svc/<name of service> <localhost port>:<service port>`. The command will open a port on your
localhost and forward traffic to a port on the service. In this case, use port `8080` for both your localhost and
service (`kubectl port-forward svc/hello-kubernetes 8080`).
Please feel free to change it to something different. Example to `9000:8080` to use port 9000 on your localhost and
forward the traffic to port 8080 on the service. Open a browser and navigate
to [http://localhost:8080](http://localhost:8080) to access your deployed application.

#### Interact with the application

Now that you can connect to the application, try and understand the web page. The webpage gives different information
about the pod that was handling your request. It displays the pod name, the namespace the pod is inside, and the node
that the pod is running on.

Try to refresh the webpage a few times and notice how the values change. You should see that the name of the pod
changes. This is because the request was routed to a different pod.

### Exercise 4 - Scaling the application

Some applications are designed to have multiple instances running. In the case of the hello-kubernetes application, you
can increase and decrease the amount of replicas with no problem. It may be desirable to scale your deployment up or
down to match the demand of the application. There are two ways to scale deployments in Kubernetes - manual, or
automatic. Automatic scaling will not be covered in this exercise.

To manually scale a deployment, you would modify the `replicas` field of the deployment resource. This can be done by
either modifying the yaml file and reapplying it, or by using the edit command. To edit the deployment using the edit
command, use the following: `kubectl edit deployment/hello-kubernetes`. This will open a window with your default text
editor. Simply modify the file, save it, and close the window to modify the resource.

1. Try to change the replica count to 5.
2. Check that the amount of pods has changed to 5
3. Try accessing the application to verify it still works
4. Change the replicas back to 3
5. Check that the amount of pods has changed to 3
6. Try accessing the application to verify it still works

When scaling the amount of replicas, the service will automatically start/stop routing traffic to the new/old pods
without disrupting existing connections.

### Exercise 5 - Deploy the application using Helm

[Helm](https://helm.sh/) is a package manager for Kubernetes. Helm simplifies the process of deploying and managing
applications on Kubernetes by providing a standardized way to package, distribute and manage Kubernetes resources. Helm
packares are called "charts". A chart is a collection of files that describes a set of Kubernetes resources along with
configurations. Charts can be customized to suit specific deployment requirements.

To install Helm go to their [install](https://helm.sh/docs/intro/install/) guide.

The hello-kubernetes application that you deployed earlier has a Helm chart. Go to the
repository [paulbouwer/hello-kubernetes](https://github.com/paulbouwer/hello-kubernetes) on GitHub and download / clone.

To install the chart using the default `values`, simply open a terminal inside the hello-kubernetes repository you just
cloned and type the command `helm install hello-kubernetes-helm ./deploy/helm/hello-kubernetes`. This will install the
Helm Chart located at `./deploy/helm/hello-kubernetes` and give the release the name "hello-kubernetes". You can see the
status of the Helm release using `helm status hello-kubernetes-helm`. Get a list of the pods and services and see what
was created.

You should see that it created 2 pods and 1 service. This is similar to the deployment you made before, except this is
installed using Helm. But now that it is installed you should try to connect to it like before, just remember that the
service is now called something different. Hint: `kubectl get services`.

A Helm chart can be configured using `values`. The default `values` can be found inside the Helm chart. Open the file
located at `./deploy/helm/hello-kubernetes/values.yaml` in the repository and see the different values. We want to try
to increase the amount of replicas using the `deployment.replicaCount` value. Because we want to modify an existing
release, we need to use the `helm upgrade` command. Use
`helm upgrade hello-kubernetes-helm ./deploy/helm/hello-kubernetes --set deployment.replicaCount=5` to set the replica
count to 5. Now get a list of the pods and notice how the amount of pods changed.

You can get a list of all Helm releases in the default namespace using the following command `helm list`.

### Exercise 6 - Interactive container

Similarly to Docker, you can interact and get a shell of a running container in Kubernetes.
First, we will try to get a shell inside an existing container. The command to execute commands inside containers is
called exec, for example `kubectl exec pods/<name of pod> -- <command>` will run a command inside a running container.
To get an interactive shell, you need to use the exec command:
`kubectl exec --stdin --tty pods/<name of pod> -- <command>`. To get a shell for one of the hello-kubernetes pods you
need to use this: `kubectl exec --stdin --tty pods/<name of pod> -- /bin/sh`.

Once you have a shell you can now run commands inside of it. Try using the `ls` command to list all files and folder
inside the current directory. You may notice that this is a Node.js application. Try to list the contents of the
`server.js` file using the `cat` command.

To exit the interactive shell write `exit` and hit the `ENTER` key or just close the terminal window.

You will now create an interactive container that is removed once you exit the shell. Run the following command:
`kubectl run ubuntu --rm -i --tty --image ubuntu -- bash`. This will create a pod called "ubuntu" that will run the
Ubuntu image. Once you exit the terminal the pod will be deleted.

Because the container is running inside the Kubernetes cluster you can now access services without using the
port-forward command.
To test this we first want to install the curl package - use `apt update && apt install curl -y` to install curl. Once
curl is installed, write the following command to send an HTTP request to the hello-kubernetes service:
`curl hello-kubernetes:8080`. The response will be the HTML for the hello-kubernetes webpage that you have seen earlier.
You can try using the command multiple times and see how the response changes.

Because the service is inside the same namespace as your ubuntu container you can use the DNS entry `hello-kubernetes`.
If you want to access a service in a different `namespace` you need to use a different `hostname`. Use the following
command `curl hello-kubernetes.default:8080` where `default` is another namespace. NB: You will notice that you are not
able to `curl` other namespaces.

Sometimes you don't want to delete the container when you exit the shell. Use the following command to create an ubuntu
container that won't be deleted when you exit the shell: `kubectl run ubuntu -i --tty --image ubuntu -- bash`. To
reattach the same shell again use one of the following command: `kubectl attach ubuntu -c ubuntu -i -t`. You can even
open two terminals and use the attach command and the shell will be shared. Try to do this and write something in one
shell and see how it is also written in the other.

You can also copy files to containers. Use the file on your localhost called `README.md`. Open a new terminal inside
same directory, and use the following command to copy the `README.md` file to the ubuntu container:
`kubectl cp README.md ubuntu:/README.md`. Open the other terminal again and use the `ls` and `cat` commands to verify
the file was copied to the container.

### Exercise 7 - Cleaning up

Kubernetes resources can be deleted using the `kubectl delete` command. You can either delete individual resources, such
as a hello-kubernetes deployment using the following command `kubectl delete deployment/hello-kubernetes`, or you can
delete it using the file you used to create the resources with using the command
`kubectl delete -f hello-kubernetes.yaml`.
> If you used Helm to create the resources then you should also delete it using Helm.

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
    1. `kubectl delete -f hello-kubernetes.yaml`
    2. `helm uninstall hello-kubernetes-helm`
    3. `kubectl delete pod ubuntu`

You can get a list of the pods and services to verify that they are deleted.

- `kubectl get all`