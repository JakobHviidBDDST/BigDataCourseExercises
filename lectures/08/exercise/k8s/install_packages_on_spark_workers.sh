#!/bin/bash

for pod in $(kubectl get pods -o name | grep -E 'spark.*worker'); do
  echo "Installing packages into /tmp/pypkgs on $pod..."
  kubectl exec "$pod" -- env HOME=/tmp pip install --no-cache-dir \
    --target /tmp/pypkgs \
    pyarrow pandas sentence-transformers \
    --extra-index-url https://download.pytorch.org/whl/cpu
done
