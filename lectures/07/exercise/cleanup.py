import subprocess

LLAMA_CPP_MANIFEST = "k8s/llama-cpp.yaml"
QDRANT_MANIFEST = "k8s/qdrant.yaml"


def run_command(command, show_output=True):
    """Run a command in the shell and print the output."""
    try:
        print(f"Executing command: {command}")
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        if show_output:
            print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError:
        print("Resources have already been deleted")


def delete_yaml_resources(file_path):
    """Delete Kubernetes resources defined in a YAML file."""
    print(f"Deleting resources defined in {file_path}...")
    run_command(f"kubectl delete -f {file_path}")


def main():
    # Today's exercises -----------------------------------------------------
    delete_yaml_resources(LLAMA_CPP_MANIFEST)
    delete_yaml_resources(QDRANT_MANIFEST)

    # Optional extras you may have created -----------------------------------
    run_command("kubectl delete pod kafka-client")

    print()
    print("Manual clean-up still needed for cluster-external state:")
    print("  1. Kafka Connect HDFS sink connector (port-forward first):")
    print("       kubectl port-forward svc/kafka-connect 8083 &")
    print("       curl -X DELETE http://127.0.0.1:8083/connectors/hdfs-sink-enriched")
    print("  2. Kafka topics (Redpanda console or kafka-delete-records):")
    print("       topics: raw-incidents, enriched-incidents")
    print("  3. HDFS artifacts, from an hdfs-cli pod (see services/hdfs):")
    print("       hdfs dfs -fs hdfs://namenode:9000 -rm -r /topics/enriched-incidents")
    print("       hdfs dfs -fs hdfs://namenode:9000 -rm -r /rag /graph")
    print()
    print("Leftovers from previous lectures (keep them if you continue tomorrow):")
    print("  - helm delete spark / kafka; kubectl delete -f ../../03/exercise/*.yaml")
    print("  - services/interactive/interactive.yaml, services/hdfs/*")


if __name__ == "__main__":
    main()
