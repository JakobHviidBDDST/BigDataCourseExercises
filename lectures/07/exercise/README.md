# Lecture 07 - Large Language Models and Scaling with Constrained Resources

The exercises for this week's lecture are about running Large Language Models and RAG pipelines on a CPU-only
cluster. You will deploy a micro-LLM (<1B parameters) with llama.cpp, stream incidents through a
Kafka → llama.cpp → HDFS pipeline, index them with PySpark + an Embedder into Qdrant, build a service-dependency
graph, and finish with a hybrid Graph-RAG query.

Please open issues [here](https://github.com/jakobhviid/BigDataCourseExercises/issues) if you encounter unclear
information or experience bugs in our examples!

## Prerequisites

| Service | How to deploy | Endpoint used today |
|---|---|---|
| HDFS | `services/hdfs` (lecture 02) | `hdfs://namenode:9000` + WebHDFS `namenode:9870` |
| Kafka + Kafka Connect + Schema Registry | Check lecture 3 exercise 1 | `kafka:9092`, `kafka-connect:8083`, `kafka-schema-registry:8081` |
| Redpanda console | Check lecture 3 exercise 3 | `kubectl port-forward svc/redpanda 8080` |
| Spark | Check lecture 04 exercise 1 | `spark://spark-master-svc:7077` |


Use the interactive pod in [services/interactive/interactive.yaml](../../../services/interactive/interactive.yaml), in the same namespace as the other services.

You can copy the exercise files from `lectures/07/exercise` on your machine like this (replace `POD_NAME` with your interactive pod's name):

```bash
kubectl cp . POD_NAME:/root/code/exercise07
```

Remember to install the dependencies inside the interactive pod, from `/root/code/exercise07`:

```bash
pip install -r requirements.txt
```

Also run `pip install setuptools` inside the interactive pod; it supplies the `distutils` module required by PySpark on Python 3.12.


### Exercise 1 - Deploy a Micro-LLM using llama.cpp

**Notice**: In a production Big Data or enterprise setting you would typically serve LLM inference with
**vLLM**: continuous batching, paged KV-cache management and GPU-optimised kernels give far higher throughput
at scale. Our cluster has no GPUs or dedicated AI accelerators - only shared CPU cores - so we use
**llama.cpp** instead: one small server binary that runs a quantised GGUF model on plain CPU threads, which
is plenty for this lab's 0.5B model. It exposes the same OpenAI-compatible API, so every script in this lab
would work unchanged against a vLLM endpoint.

**Task**: Deploy the llama.cpp server and wait until it is ready:

```bash
kubectl apply -f k8s/llama-cpp.yaml
```

**Notice**: The model download plus CPU warmup takes around 5-10 minutes. You can check if the deployment is ready by running the following command:

```bash
kubectl rollout status deploy/llama-cpp
```

**Task**: After the pod is ready, you can verify the OpenAI-compatible API:

```bash
kubectl port-forward svc/llama-cpp 8000
curl http://127.0.0.1:8000/v1/models
```

**Task**: Try and send a simple query to the LLM:

```bash
curl http://127.0.0.1:8000/v1/chat/completions -H 'Content-Type: application/json' -d '{
  "model": "qwen2.5-0.5b-instruct-q8_0.gguf",
  "messages": [{"role": "user", "content": "In one sentence: what is a KV cache?"}],
  "max_tokens": 64, "temperature": 0
}'
```

**Notice**: To swap the model, edit the `--hf-repo` and `--hf-file` args in [k8s/llama-cpp.yaml](./k8s/llama-cpp.yaml) and redeploy, e.g. `--hf-repo HuggingFaceTB/SmolLM2-360M-Instruct-GGUF` with `--hf-file smollm2-360m-instruct-q8_0.gguf`. The server downloads the GGUF file from Hugging Face on startup.


### Exercise 2 - Tagging incidents from the terminal

In this exercise you will use the LLM for giving tags to a set of fictional terminal incidents. The script [`starter/task2_tag_terminal.py`](./starter/task2_tag_terminal.py) handles the JSON schema of the terminal incients, but only uses a placeholder prompt. Your job will be to define this system prompt. The predefined terminal incidents can be found in [`data/sample_incidents.jsonl`](data/sample_incidents.jsonl).

**Task**: Run the script as-is inside an interactive pod, with the placeholder prompt untouched, against the LLM and look at the tag table it prints:

```bash
python3 starter/task2_tag_terminal.py
```

You should see an output like this with 50 different incidents:
```text
ticket_id  category   severity  source_service     target_dependency
INC-001    Network    MEDIUM    checkout-service   auth-service
...
```

**Task**: Write the `SYSTEM_PROMPT` (TODO 2.1 in [`starter/task2_tag_terminal.py`](./starter/task2_tag_terminal.py)). The schema enforces field names and enums, so your prompt must supply the semantics it cannot express:

| Field | What your prompt has to define |
|---|---|
| `category` | what kind of problem belongs in `Network` / `Database` / `Auth` / `Deployment` / `Memory` |
| `severity` | what deserves `LOW` vs `MEDIUM` vs `CRITICAL` |
| `source_service` | the logs name many services, which one is the reporting one |
| `target_dependency` | which one failed as a dependency - and when is `none` the right answer |

**Task**: Run the script again, and compare it with the initial run. Are the source_services correct now? Does the severify reflect what you would say is important? Remember that the LLM is very small and therefore might get a lot of it wrong if not helped.

**Task**: Try and run the [`solution/task2_tag_terminal.py`](./solution/task2_tag_terminal.py) file, and check its `SYSTEM_PROMPT` against yours. Did you miss something?

### Exercise 3 - Streaming pipeline: Kafka → llama.cpp → Kafka → HDFS

**Task**: Make sure Kafka and HDFS are running within your namespace.

**Task**: Create two topics in the Redpanda console: `raw-incidents` and `enriched-incidents` (1 partition, replication factor 1).

**Task**: Run the producer, then the enricher:

```bash
python3 starter/task3_produce_raw.py            # publishes 50 tickets to raw-incidents
python3 starter/task3_kafka_llama_enricher.py   # tags every ticket and publishes it to enriched-incidents
```

Watch the `enriched-incidents` topic in Redpanda for the tickets with tags applied. Eeach output event is a record from the `raw-incidents` plus an `"llm"` object containing the same tags as in the previous exercise.

**Notice**: The consumer settings in the enricher (`max_poll_records=4`, 5 minute poll interval, manual
commits) are deliberate because CPU inference is slow. With GPU processing this value could easily be increased.

**Task**: Register the pre-configured Kafka Connect HDFS sink:

```bash
kubectl port-forward svc/kafka-connect 8083
curl -X POST http://127.0.0.1:8083/connectors \
  -H 'Content-Type: application/json' \
  -d @solution/hdfs-sink-enriched.json
```

**Task**: Verify the sink wrote to HDFS and check the connector consumer lag in Redpanda:

```bash
hdfs dfs -fs hdfs://namenode:9000 -ls -R /topics/enriched-incidents
```

**Task**: Try and kill the enricher with `Ctrl-C` while it is processing and restart it. What lands on the output
topic this time, and why?

**Hint**: Is any of the data duplicated?

### Exercise 4 - Scalable RAG indexing: Embedders into Qdrant + a Graph

**Task**: Deploy the vector database:

```bash
kubectl apply -f k8s/qdrant.yaml
kubectl port-forward svc/qdrant 6333    # dashboard: http://127.0.0.1:6333/dashboard
```

**Task**: To access the qdrang dashboard, open http://127.0.0.1:6333/dashboard after you have port-forwarded the service.

**Task**: The indexer `starter/task4_spark_rag_indexer.py` is complete and runs as given. It reads the JSON files from the HDFS sink, embeds every incident's `raw_text` with a small bi-encoder inside Spark (`mapInPandas`), upserts 384-dimensional points into the Qdrant collection `incidents`, and writes the service-dependency tables (`vertices`, `edges`) as Parquet to `hdfs:///graph/services/`. Read the docstring before running it as it explains why an embedder is used instead of the chat model.

**Notice**: The embedding is computed with the bi-encoder inside the Spark job, not with the llama.cpp chat model from Exercise 1 (the job docstring explains why).

**Task**: Prepare the Spark Workers to work with the Python scripts by running the following shell script on your machine (outside the interactive container), from `lectures/07/exercise`, where `kubectl` is configured:

```bash
bash ./k8s/install_packages_on_spark_workers.sh
```

**Task**: Run the indexer on the cluster within the interactive container:

```bash
spark-submit --conf "spark.executorEnv.PYTHONPATH=/tmp/pypkgs" --conf "spark.executorEnv.HF_HOME=/tmp/hf_cache" --conf "spark.executorEnv.HOME=/tmp" --py-files starter/embeddings.py,starter/utils.py starter/task4_spark_rag_indexer.py
```

**Task**: Inspect your work: the point count in the Qdrant dashboard and the edge table that was written:

```bash
hdfs dfs -fs hdfs://namenode:9000 -cat /graph/services/edges_json/*
```

You should see edges like `payment-gateway -> checkout-service` and `postgres-orders -> payment-gateway`; however, your results may be a bit different.

### Exercise 5 - Hybrid retrieval: Vector RAG vs. Graph-RAG

In this final exercise you will retrieve data from the Graph-RAG and compare it with a Vector RAG.

**Task**: Run the complete `starter/task5_hybrid_rag_query.py` inside the interactive container:

```bash
python3 starter/task5_hybrid_rag_query.py   # defaults to the 504 root-cause question
```

The script retrieves the top-K incidents by vector similarity, expands the search by following failing dependencies in the service graph (each hop = one dependency deeper), and asks llama.cpp the same question twice, once with each context, and prints the two answers side by side.

The expected output should look something like this (you might get a different result):

```text
===== VECTOR-ONLY RAG (semantic top-K) =====
  INC-017   CRITICAL Auth       checkout-service -> auth-service    score=...
  ...
===== GRAPH-RAG EXPANSION (2-hop over service graph) =====
  INC-042   CRITICAL Memory     redis-cluster-02 -> none   [graph hop 2 via redis-cluster-02]
===== VERDICT =====
  >> Vector-only RAG MISSES INC-042; Graph-RAG recovers them (incl. CRITICAL root cause!).
```

**Task**: Try and run the following commands with different configurations and note what changed in the retrieved context:

```bash
python3 starter/task5_hybrid_rag_query.py --hops 1        # does 1 hop reach redis?
python3 starter/task5_hybrid_rag_query.py --k 10          # can top-K alone find INC-042?
python3 starter/task5_hybrid_rag_query.py --graph-min-severity MEDIUM
python3 starter/task5_hybrid_rag_query.py --query "redis cluster out of memory killed process"
```

## Step-by-step guide to clean up

### Automated clean up

**Windows**: `python cleanup.py`

**MacOS / Linux**: `python3 cleanup.py`

It deletes today's `llama-cpp` and `qdrant` resources and prints the remaining manual steps (connector,
topics, HDFS directories).

### Manual clean up

- Today's exercises:
    1. `kubectl delete -f k8s/llama-cpp.yaml`
    2. `kubectl delete -f k8s/qdrant.yaml` (includes `qdrant-pvc`)
    3. `curl -X DELETE http://127.0.0.1:8083/connectors/hdfs-sink-enriched` (after port-forward)
    4. Delete topics `raw-incidents`, `enriched-incidents` in Redpanda
    5. From an hdfs-cli pod: `hdfs dfs -fs hdfs://namenode:9000 -rm -r /topics/enriched-incidents /rag /graph`
- Previous lectures (keep if you continue tomorrow): `helm delete spark`, `helm delete kafka`,
  `services/interactive`, `services/hdfs` - see earlier exercise READMEs.
