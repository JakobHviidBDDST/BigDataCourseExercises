#!/bin/bash

# Accept server and namespace as arguments
SERVER=$1
NAMESPACE=$2
SERVICE_ACCOUNT=$3

# Variables
SERVICE_ACCOUNT="${SERVICE_ACCOUNT}-sa"
ROLE="${NAMESPACE}-role"
ROLE_BINDING="${SERVICE_ACCOUNT}-${NAMESPACE}-rolebinding"
CLUSTER_SCOPED_ROLE="cluster-scoped-read"
VIEW_BINDING="${NAMESPACE}-view-binding"
CLUSTER_SCOPED_BINDING="${NAMESPACE}-cluster-scoped-read-binding"
OLD_CLUSTER_ROLE_BINDING="${NAMESPACE}-view-clusterrolebinding"
SECRET_NAME="${SERVICE_ACCOUNT}-manual-secret"
CA_CERT="/var/snap/microk8s/current/certs/ca.crt"
KUBECONFIG_DIR="tmp"

# Create namespace if it doesn't exist
microk8s kubectl get namespace $NAMESPACE || microk8s kubectl create namespace $NAMESPACE || { echo "Failed to create namespace. Exiting."; exit 1; }

# Create ServiceAccount if it doesn't exist
microk8s kubectl get serviceaccount $SERVICE_ACCOUNT -n $NAMESPACE || microk8s kubectl create serviceaccount $SERVICE_ACCOUNT -n $NAMESPACE || { echo "Failed to create ServiceAccount. Exiting."; exit 1; }


# Create Role for full CRUD permissions denoted by (*) within the specific namespace
cat <<EOF | microk8s kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: $NAMESPACE
  name: $ROLE
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch", "create", "update", "delete", "patch"]
EOF

# Create RoleBinding for full CRUD permissions within the specific namespace
cat <<EOF | microk8s kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: $ROLE_BINDING
  namespace: $NAMESPACE
subjects:
- kind: ServiceAccount
  name: $SERVICE_ACCOUNT
  namespace: $NAMESPACE
roleRef:
  kind: Role
  name: $ROLE
  apiGroup: rbac.authorization.k8s.io
EOF


# Remove the old cluster-wide binding to the custom read-all ClusterRole, which also exposed Secrets in every
# namespace. The roleRef of a binding is immutable, so the new bindings below use new names.
microk8s kubectl delete clusterrolebinding $OLD_CLUSTER_ROLE_BINDING --ignore-not-found

# Read-only access to namespaced resources in all namespaces, using the built-in "view" ClusterRole.
# "view" deliberately excludes Secrets (and RBAC objects), so other students' tokens stay private.
cat <<EOF | microk8s kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: $VIEW_BINDING
subjects:
- kind: ServiceAccount
  name: $SERVICE_ACCOUNT
  namespace: $NAMESPACE
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
EOF

# ClusterRole for read-only access to the few cluster-scoped resources students need (e.g. kubectl get nodes)
cat <<EOF | microk8s kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: $CLUSTER_SCOPED_ROLE
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces", "persistentvolumes"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["storage.k8s.io"]
  resources: ["storageclasses"]
  verbs: ["get", "list", "watch"]
EOF

# Create ClusterRoleBinding for the cluster-scoped read-only permissions
cat <<EOF | microk8s kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: $CLUSTER_SCOPED_BINDING
subjects:
- kind: ServiceAccount
  name: $SERVICE_ACCOUNT
  namespace: $NAMESPACE
roleRef:
  kind: ClusterRole
  name: $CLUSTER_SCOPED_ROLE
  apiGroup: rbac.authorization.k8s.io
EOF

# Manually create the secret with proper annotations
cat <<EOF | microk8s kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: $SECRET_NAME
  namespace: $NAMESPACE
  annotations:
    kubernetes.io/service-account.name: $SERVICE_ACCOUNT
type: kubernetes.io/service-account-token
EOF

# Wait for the secret to be populated
sleep 10

# Extract the token from the secret
TOKEN=$(microk8s kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath="{.data.token}" | base64 --decode) || { echo "Failed to retrieve token. Exiting."; exit 1; }

# Ensure TOKEN is available
if [ -z "$TOKEN" ]; then
  echo "Error: Token not found or created for ServiceAccount $SERVICE_ACCOUNT in namespace $NAMESPACE"
  exit 1
else
  echo "Token for ServiceAccount $SERVICE_ACCOUNT in namespace $NAMESPACE created"
fi

# Verify that the ServiceAccount cannot read Secrets outside its own namespace
if microk8s kubectl auth can-i get secrets -n kube-system --as=system:serviceaccount:$NAMESPACE:$SERVICE_ACCOUNT | grep -q yes; then
  echo "Warning: $SERVICE_ACCOUNT can read Secrets in other namespaces. Check the cluster role bindings."
fi

# Extract the certificate authority data
CERTIFICATE_AUTHORITY_DATA=$(cat $CA_CERT | base64 | tr -d '\n') || { echo "Failed to read CA certificate. Exiting."; exit 1; }

# Create kubeconfig directory if not exists
mkdir -p $KUBECONFIG_DIR

# Create kubeconfig file
KUBECONFIG_FILE="$KUBECONFIG_DIR/$SERVICE_ACCOUNT-$NAMESPACE-kubeconfig.yaml"
cat <<EOF > $KUBECONFIG_FILE
apiVersion: v1
kind: Config
clusters:
- cluster:
    certificate-authority-data: ${CERTIFICATE_AUTHORITY_DATA}
    server: ${SERVER}
  name: microk8s-cluster
contexts:
- context:
    cluster: microk8s-cluster
    namespace: $NAMESPACE
    user: $SERVICE_ACCOUNT
  name: $NAMESPACE-context
current-context: $NAMESPACE-context
users:
- name: $SERVICE_ACCOUNT
  user:
    token: ${TOKEN}
EOF

echo "Kubeconfig file for $NAMESPACE created successfully at $KUBECONFIG_FILE"
