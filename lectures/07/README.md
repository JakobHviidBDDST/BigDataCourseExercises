# Lecture 07 - Metadata, Data Provenance and Data Mesh

This week's exercises will follow the case-based structure explained in the overview from Lecture 01's exercise. To summarize the process:

- You will receive a case that needs solving.
- You should design the architecture that you believe can solve this problem (use your preferred drawing tool, such as draw.io, Excalidraw, etc.).
  - Ideally, use the technologies covered in the course so far.
  - You will get feedback on your proposed architecture from the instructors.
- Once you've drawn the architecture, try to assemble it using the chosen technologies and blueprints.

The process can be visualized as follows:

```mermaid
flowchart LR
    start@{ shape: circle, label: "Start" }
    case@{ shape: doc, label: "Read the case" }
    arch@{ shape: docs, label: "Draw your proposed architecture for the case" }
    feedback@{ shape: note, label: "Get feedback on your architecture from the instructors" }
    impl@{ shape: processes, label: "Implement architecture in Kubernetes" }
    test@{ shape: process, label: "Test architecture" }

    stop@{ shape: dbl-circ, label: "Done" }


    start-->case-->arch-->impl-->test
    arch-->feedback-->arch

    test-->|"If not compliant with the requirements"|arch
    test-->|"If compliant with the requirements"|stop
```

## New Technologies

The new technologies introduced this week are: **Hive, MongoDB, Redis**.

For some general quick start guidance on utilising the technologies, please view the archived exercises from [Lecture 07 E24](https://github.com/JakobHviidBDDST/BigDataCourseExercises/tree/main/archive/E24/07).
