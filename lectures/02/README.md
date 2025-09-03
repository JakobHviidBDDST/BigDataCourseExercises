# Lecture 02 - HDFS and different file formats

This week's exercises will be using the case based structure described in the general overview from lecture 01's exercise:

- You will be presented with a case that needs to be solved
- You must draw up the architecture you deem can solve this solution (use your prefered drawing tool, e.g. draw.io, Excalidraw, etc.)
    - Ideally using the technologies seen in the course so far
- Once the architecture has beeen drawn, attempt to assemble it with the chosen technologies

The new technologies introduced this week are: **HDFS, Avro and Parquet**

For some general quick start guidance on utilising the technologies, please view the archived exerises from [Lecture 02 E24](https://github.com/JakobHviidBDDST/BigDataCourseExercises/tree/main/archive/E24/02)

# The Case

The Company ReadBooks incorporated needs to store static data containing the contents of books, they also want to analyze and present data such as word counts for specific books and overall word counts.

### Solution requirements
- The solution must store books with their names and their whole contents
- The solution must ingest the data into a distributed filesystem
- The solution should be able to store 10.000+ books
- The solution should have means to efficiently query word counts by various criteria

### Remember to
- Identify bottlenecks
- Pick appropriate data format
- Consider how scalability will be handled
- Address data flow
- Address how processed results will be accessed/presented