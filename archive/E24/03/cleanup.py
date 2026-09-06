import subprocess
import platform
import json
import time

KAFKA_CLIENT_IMAGE = "docker.io/bitnamilegacy/kafka:3.8.0-debian-12-r3"
PYTHON_IMAGE = "python"
HDFS_SERVICES_PATH = "../../../services/hdfs"
INTERACTIVE_DEPLOYMENT_PATH = "../../../services/interactive/interactive.yaml"
TIME_TO_SLEEP = 3


def run_command(command, show_output=True):
    """Run a command in the shell and print the output."""
    try:
        print(f"Executing command: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if show_output:
            print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Resources have already been deleted")


def get_pod_name_by_image(image_name):
    """Get the name of the pod running a specified image."""
    print(f"Searching for pod running image: {image_name}")
    pods_info = run_command("kubectl get pods -o json", False)
    if pods_info:
        pods = json.loads(pods_info).get('items', [])
        for pod in pods:
            containers = pod.get('spec', {}).get('containers', [])
            for container in containers:
                if image_name in container.get('image', ''):
                    pod_name = pod.get('metadata', {}).get('name', '')
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


def cleanup():
    print("Starting cleanup process...")

    # Step 1: Delete created pods image and interactive container
    delete_pod_by_image(KAFKA_CLIENT_IMAGE)
    delete_pod_by_image(PYTHON_IMAGE)
    delete_interactive_container()

    # Step 2: Delete Sqoop
    delete_yaml_resources("sqoop.yaml")

    # Step 3: Delete Postgres resources
    delete_helm_resource("postgresql")
    delete_pvc_resource("data-postgresql-0")

    # Step 4: Delete Flume
    delete_yaml_resources("flume.yaml")

    # Step 5: Delete Kafka resources
    delete_yaml_resources("redpanda.yaml")
    delete_yaml_resources("kafka-schema-registry.yaml")
    delete_yaml_resources("kafka-connect.yaml")
    delete_yaml_resources("kafka-ksqldb.yaml")
    delete_helm_resource("kafka")
    delete_pvc_resource("data-kafka-controller-0 data-kafka-controller-1 data-kafka-controller-2")

    # Step 6: Delete HDFS resources
    delete_hdfs_resources()

    # Wait 3 seconds for all resources to be deleted
    print(f"Waiting {TIME_TO_SLEEP} seconds to resources to be deleted")
    time.sleep(TIME_TO_SLEEP)

    # Verify deletion by listing the remaining pods and services
    print("Verifying remaining resources...")
    run_command("kubectl get all")

    print("Cleanup completed.")


if __name__ == "__main__":
    cleanup()
