# Big Data and Data Science Technology, E25 course exercises

This repository contains the exercises related to the course [Big Data and Data Science Technology, E25](https://odin.sdu.dk/sitecore/index.php?a=fagbesk&id=138236&listid=18884&lang=en) at University of Southern Denmark.

## Instructors

This year's instructors are Oliver Feldborg Hansen and Anders Launer Bæk-Petersen, who completed the course in E24 and E22, respectively. We will facilitate the exercise hours and are available on the announced Discord channel for this course. An invitation link to the Discord channel will be provided in the first lecture.
We encourage you to provide open and direct feedback throughout the semester. Please feel free to open new GitHub issues for bugs, etc. [here](https://github.com/jakobhviid/BigDataCourseExercises/issues) if you encounter unclear information or experience bugs in our examples!

## Objective

The goal of these exercises is to guide you through the practical parts of the curriculum. The structure of this year’s exercises was inspired by the architecture lecture in the course. We previously moved from a Docker Compose setup to a Kubernetes-based one.

Our main focus this semester is twofold:

- Develop an exercise framework where we create diagrams of the architecture before starting implementation.
- Start exercises that provide hands-on experience with Kubernetes and the tools commonly used in Big Data and Data Science fields.

## Connect to the shared Kubernetes cluster

You will be using a shared Kubernetes cluster for the exercises hosted by the university. All the exercises are designed to be run from your localhost using `kubectl` commands.

You will be provided with a `kubeconfig` file that you can use to connect to the cluster before the first exercise session, provided you are on the SDU network.
If you are not on the SDU network, you can use a VPN connection to access it. You can find more information about the VPN connection [here](https://any2.sdu.dk).

Information about the `kubeconfig` file(s) can be discovered here: [Configure Access to Multiple Clusters](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/). For further details, please look into [Organizing Cluster Access Using kubeconfig Files](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) if you need to manage multiple Kubernetes clusters in your environment.

## Content of the repository

The repository will contain materials from previous semesters and the exercises for the current semester. The folders `archive` and `services` contain material from the previous semesters. The `lectures` folder contains the material for the current semester.

```text
.
├── archive
│   ├── E22
│   ├── E23
│   └── E24
├── infrastructure
│   ├── create-admin-kubeconfig.sh
│   ├── create-user.sh
│   ├── create-users.sh
│   ├── delete-users.sh
│   ├── images
│   │   ├── __init__.py
│   │   ├── images.txt
│   │   ├── persist-images.py
│   │   ├── README.md
│   │   ├── side-load.py
│   │   ├── side-load.sh
│   │   └── utils.py
│   ├── parse_its.py
│   ├── README.md
│   └── share_kubeconfigs
│       ├── parse_groups.ipynb
│       ├── parse_students copy.ipynb
│       ├── parse_students.ipynb
│       ├── sent_msg_groups.py
│       ├── sent_msg_students.py
│       ├── sent_msg.ipynb
│       └── src
│           ├── __init__.py
│           ├── groups.py
│           ├── msg.py
│           └── students.py
├── lectures
│   └── {01, 02, ..., 07}
│       └── README.md
├── LICENSE
├── README.md
└── services
    ├── atlas
    ├── hdfs
    │   ├── configmap.yaml
    │   ├── datanodes.yaml
    │   ├── hdfs-cli.yaml
    │   ├── namenode.yaml
    │   └── README.md
    ├── interactive
    │   ├── Dockerfile
    │   ├── interactive.yaml
    │   ├── README.md
    │   └── requirements.txt
    ├── kafka-connect
    │   ├── Dockerfile
    │   └── README.md
    └── README.md
```
