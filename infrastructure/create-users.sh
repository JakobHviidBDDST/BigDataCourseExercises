#!/bin/bash

# Check if the server IP argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <server-ip>"
  exit 1
fi

SERVER_IP=$1
# SERVER_IP="10.123.3.156"
SERVER="https://${SERVER_IP}:16443"

echo "Create kubeconfigs!"

while read -r NAMESPACE
do 
  ./create-user.sh "$SERVER" "$NAMESPACE" "$NAMESPACE"
done <users.txt