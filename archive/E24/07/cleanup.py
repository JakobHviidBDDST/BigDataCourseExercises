import json
import subprocess
import time

REDIS_CLUSTER_CLIENT_IMAGE = "docker.io/bitnami/redis-cluster:7.4.0-debian-12-r1"
KAFKA_PATH = "../03/"
HDFS_SERVICES_PATH = "../../../services/hdfs"
INTERACTIVE_DEPLOYMENT_PATH = "../../../services/interactive/interactive.yaml"
TIME_TO_SLEEP = 3


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
    except subprocess.CalledProcessError as e:
        print("Resources have already been deleted")


def get_pod_name_by_image(image_name):
    """Get the name of the pod running a specified image."""
    print(f"Searching for pod running image: {image_name}")
    pods_info = run_command("kubectl get pods -o json", False)
    if pods_info:
        pods = json.loads(pods_info).get("items", [])
        for pod in pods:
            containers = pod.get("spec", {}).get("containers", [])
            for container in containers:
                if image_name in container.get("image", ""):
                    pod_name = pod.get("metadata", {}).get("name", "")
                    print(f"Found pod: {pod_name} running image: {image_name}")
                    return pod_name
    print(f"No pod found running image: {image_name}")
    return None


def delete_pod_by_image(image_name):
    """Delete a pod running a specified image."""
    pod_name = get_pod_name_by_image(image_name)
    if pod_name:
        print(f"Deleting pod: {pod_name}")
        run_command(f"kubectl delete pod {pod_name}")
    else:
        print(f"No pod found to delete for image: {image_name}")


def delete_hdfs_resources():
    """Delete Kubernetes resources defined HDFS services directory."""
    print(f"Deleting resources defined in {HDFS_SERVICES_PATH}...")
    run_command(f"kubectl delete -f {HDFS_SERVICES_PATH}")


def delete_kafka_resources():
    """Delete Kubernetes resources defined Kafka Lecture 3 directory."""
    print(f"Deleting resources defined in {KAFKA_PATH}...")
    delete_yaml_resources(f"{KAFKA_PATH}redpanda.yaml")
    delete_yaml_resources(f"{KAFKA_PATH}kafka-schema-registry.yaml")
    delete_yaml_resources(f"{KAFKA_PATH}kafka-connect.yaml")
    delete_yaml_resources(f"{KAFKA_PATH}kafka-ksqldb.yaml")
    delete_helm_resource("kafka")
    delete_pvc_resource(
        "data-kafka-controller-0 data-kafka-controller-1 data-kafka-controller-2"
    )


def delete_interactive_container():
    """Delete Kubernetes resources defined in interactive services directory"""
    print(f"Deleting resources defined in {INTERACTIVE_DEPLOYMENT_PATH}...")
    run_command(f"kubectl delete -f {INTERACTIVE_DEPLOYMENT_PATH}")


def delete_yaml_resources(file_path):
    """Delete Kubernetes resources defined in a YAML file."""
    print(f"Deleting resources defined in {file_path}...")
    run_command(f"kubectl delete -f {file_path}")


def delete_helm_resource(release_name):
    """Delete a Helm release."""
    print(f"Uninstalling Helm release: {release_name}...")
    run_command(f"helm uninstall {release_name}")


def delete_pvc_resource(pvc_name):
    """Delete a Persistent Volume Claim (PVC)"""
    print(f"Uninstalling PVC: {pvc_name}...")
    run_command(f"kubectl delete pvc {pvc_name}")


def delete_secret(secret_name):
    """Delete a Kubernetes secret."""
    print(f"Deleting secret: {secret_name}")
    run_command(f"kubectl delete secret {secret_name}")


def cleanup():
    print("Starting cleanup process...")

    # Step 1: Clean leftover resources from Acryl Data and LinkedIn DataHub setup
    run_command("kubectl delete pod --field-selector=status.phase==Succeeded")
    run_command("kubectl delete pod --field-selector=status.phase==Failed")
    run_command("kubectl delete jobs --field-selector=status.successful=1")

    # Step 2: Acryl Data and LinkedIn DataHub resources
    delete_helm_resource("datahub")
    delete_helm_resource("prerequisites")
    delete_secret("mysql-secrets neo4j-secrets")
    delete_pvc_resource(
        "data-prerequisites-mysql-0 "
        "data-prerequisites-neo4j-0 "
        "elasticsearch-master-elasticsearch-master-0 "
        "data-prerequisites-kafka-broker-0 "
        "data-prerequisites-zookeeper-0 "
    )

    # Step 3: Delete Kafka resources
    delete_kafka_resources()

    # Wait 3 seconds for all resources to be deleted
    print(f"Waiting {TIME_TO_SLEEP} seconds to resources to be deleted")
    time.sleep(TIME_TO_SLEEP)

    # Verify deletion by listing the remaining pods and services
    print("Verifying remaining resources...")
    run_command("kubectl get all")

    print("Cleanup completed.")


if __name__ == "__main__":
    cleanup()
