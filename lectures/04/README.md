# Lecture 04 - Spark

This week's exercises will use the case-based structure described in the general overview from Lecture 01's exercise. To summarize the process:

- You will be presented with a case that needs solving.
- You must design the architecture you believe can solve this problem (use your preferred drawing tool, e.g., draw.io, Excalidraw, etc.).
  - Ideally, using the technologies covered in the course so far.
  - You will receive feedback on your proposed architecture from the instructors.
- Once the architecture has been drawn, try to assemble it using the selected technologies and blueprints.

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

The new technologies introduced this week are: **Spark, Spark SQL and Spark Streaming**.

For some general quick start guidance on utilising the technologies, please view the archived exerises from [Lecture 04 E24](https://github.com/JakobHviidBDDST/BigDataCourseExercises/tree/main/archive/E24/04).

## Case Description