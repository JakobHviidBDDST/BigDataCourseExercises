ARG CP_VERSION=7.3.1
FROM confluentinc/cp-server-connect-base:${CP_VERSION}
RUN confluent-hub install --no-prompt mongodb/kafka-connect-mongodb:1.8.0
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:latest
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-hdfs:latest
RUN confluent-hub install --no-prompt jcustenborder/kafka-connect-redis:latest
