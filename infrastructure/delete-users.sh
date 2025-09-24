#!/bin/bash
TMPFILE="namespaces.txt"

microk8s kubectl get ns  --no-headers -o custom-columns=":metadata.name" > $TMPFILE



declare -a ns_keep=(
  "default" 
  "cert-manager"
  "kube-node-lease"
  "kube-public"
  "kube-system"
  "observability")

while  IFS= read -r value; 
do
  if [[ ${ns_keep[@]} =~ $value ]]
  then
    echo "value to keep:    " $value
  else
    echo "value to delete:  " $value
    microk8s kubectl delete all --all -n $value
    # microk8s kubectl delete serviceaccount,role,rolebinding,secret --all -n $value
    # microk8s kubectl delete ns $value
  fi
done < $TMPFILE

rm $TMPFILE