#!/bin/bash

# Check if the server IP argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <server-ip>"
  exit 1
fi

SERVER_IP=$1
SERVER="https://${SERVER_IP}:16443"

echo "Create kubeconfigs!"
while read NAMESPACE; do
  ./create-user.sh "$SERVER" "$NAMESPACE"
done <users.txt