# Lecture 04 - Spark

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

The new technologies introduced this week are: **Spark, Spark SQL and Spark Streaming**.

For some general quick start guidance on utilising the technologies, please view the archived exercises from [Lecture 04 E24](https://github.com/JakobHviidBDDST/BigDataCourseExercises/tree/main/archive/E24/04).

## Case Description

Remember PowerGrid Analytics LLC? Well, they definitely remember you! And they're back for more. After your previous excellent work, a *spark* has ignited during a C-suite meeting, and they've hired you again, this time to assist with distributed data processing!

There are several objectives they want you to achieve:

Remember that unorganized employee data? Well, apparently those are quite long and detailed reports, and they want the counts of specific words from the reports stored in long-term storage.

Additionally, they want to perform some calculations with their wattage data that they measure. First, they want you to calculate the averages of the sample values of the wattage data stored in long-term storage. Second, they also want to do this live during ingestion, directly from the Kafka topic you are ingesting from!

NB: Remember that the theme of today's exercises is **Spark**, if you find the case's goals hard to understand, have a look at the archived exercise ;)

### Solution Requirements

- The solution must be able to analyze text files from long-term storage.
- The solution must be able to find the average sample values of the data stored in long-term storage and the live data being ingested.

### Demonstrate

- How to analyze text files in long-term storage, and get the specific word counts.
- How to find the average sample values of data in long-term storage.
- How to find the average sample values of data from a topic in a streaming platform.

### Remember to

- Identify bottlenecks.
- Consider how scalability will be managed.
- Address data flow.
- Present arguments for and discuss:
  - The use of **Spark** for these tasks compared to previous technologies.
