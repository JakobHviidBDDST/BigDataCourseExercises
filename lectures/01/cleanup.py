import subprocess
import platform
import json
import time

UBUNTU_IMAGE = "ubuntu"
INTERACTIVE_DEPLOYMENT_PATH = "../../services/interactive/interactive.yaml"
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


def delete_yaml_resources(file_path):
    """Delete Kubernetes resources defined in a YAML file."""
    print(f"Deleting resources defined in {file_path}...")
    run_command(f"kubectl delete -f {file_path}")


def delete_helm_resource(release_name):
    """Delete a Helm release."""
    print(f"Uninstalling Helm release: {release_name}...")
    run_command(f"helm uninstall {release_name}")


def delete_interactive_container():
    """Delete Kubernetes resources defined in interactive services directory"""
    print(f"Deleting resources defined in {INTERACTIVE_DEPLOYMENT_PATH}...")
    run_command(f"kubectl delete -f {INTERACTIVE_DEPLOYMENT_PATH}")


def cleanup():
    print("Starting cleanup process...")

    # Step 1: Delete the interactive pod based on the ubuntu image or custom interactive container
    delete_pod_by_image(UBUNTU_IMAGE)
    delete_interactive_container()

    # Step 2: Delete the hello-kubernetes deployment
    delete_yaml_resources("hello-kubernetes.yaml")

    # Step 3: Uninstall the hello-kubernetes Helm release
    delete_helm_resource("hello-kubernetes-helm")

    # Wait 3 seconds for all resources to be deleted
    print(f"Waiting {TIME_TO_SLEEP} seconds to resources to be deleted")
    time.sleep(TIME_TO_SLEEP)

    # Verify deletion by listing the remaining pods and services
    print("Verifying remaining resources...")
    run_command("kubectl get all")

    print("Cleanup completed.")


if __name__ == "__main__":
    cleanup()
