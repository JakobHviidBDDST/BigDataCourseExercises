# Kafka Connect

This folder includes the build recipe and components for the used image running with the following pre-built connectors:
- [mongodb/kafka-connect-mongodb:1.8.0](https://www.confluent.io/hub/mongodb/kafka-connect-mongodb)
- [confluentinc/kafka-connect-jdbc:latest](https://www.confluent.io/hub/confluentinc/kafka-connect-jdbc)
- [confluentinc/kafka-connect-hdfs:latest](https://docs.confluent.io/kafka-connectors/hdfs/current/overview.html)

This image is based on `confluentinc/cp-server-connect-base:7.3.1` and the above-mentioned connectors have been added to extend the base image. Please look into the [Dockerfile](./Dockerfile) for greater context.
