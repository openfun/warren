# Warren Helm Chart

## Dependencies

- A running Kubernetes cluster
- `kubectl`, the official Kubernetes CLI: https://kubernetes.io/docs/reference/kubectl/
- `helm`, the package manager for kubernetes: https://helm.sh/fr/docs/intro/install/


## Overview

In this tutorial, we'll deploy Warren and all other tools required for a
complete learning analytics stack:

1. A data lake that stores learning records: we choose Elasticsearch,
2. A Learning Records Store (LRS) that receives and sends learning records in xAPI
   format _via_ an HTTP API,
3. A dashboard suite that calculates indicators and provides an interface to visualize
   them.

## Deploy Warren to k8s using Helm

TODO.

## Working on the Helm Chart

> :bulb: While working on the Helm Chart, suggested commands suppose that your
> current directory is `./src/helm`.

We recommend using [Minikube](https://minikube.sigs.k8s.io/docs/start/) to run a
local cluster that we will deploy Warren on.

```bash
# Start a local kubernetes cluster
minikube start
```

We will now create our own Kubernetes namespace to work on:

```bash
# This is our namespace
export K8S_NAMESPACE="learning-analytics"

# Check your namespace value
echo ${K8S_NAMESPACE}

# Create the namespace
kubectl create namespace ${K8S_NAMESPACE}

# Activate the namespace
kubectl config set-context --current --namespace=${K8S_NAMESPACE}
```

### Deploy the data lake: Elasticsearch

In its recent releases, Elastic recommends deploying its services using Custom
Resource Definitions (CRDs) installed via its official Helm chart. We will
first install the Elasticsearch (ECK) operator cluster-wide:

```bash
# Add elastic official helm charts repository
helm repo add elastic https://helm.elastic.co

# Update available charts list
helm repo update

# Install the ECK operator
helm install elastic-operator elastic/eck-operator -n elastic-system --create-namespace
```

Since CRDs are already deployed cluster-wide, we will now be able to deploy a
two-nodes elasticsearch "cluster":

```bash
kubectl apply -f manifests/data-lake.yml
```

Once applied, your elasticsearch pod should be running. You can check this
using the following command:

```bash
kubectl get pods -w
```

We expect to see two pods called `data-lake-es-default-0` and `data-lake-es-default-1`.

When our Elasticsearch cluster is up (this can take few minutes), you may
create the Elasticsearch index that will be used to store learning traces (xAPI
statements):

```bash
# Store elastic user password
export ELASTIC_PASSWORD="$(kubectl get secret data-lake-es-elastic-user -o jsonpath="{.data.elastic}" | base64 -d)"

# Execute an index creation request in the elasticsearch container
kubectl exec data-lake-es-default-0 --container elasticsearch -- \
    curl -ks -X PUT "https://elastic:${ELASTIC_PASSWORD}@localhost:9200/statements?pretty"
```

Our Elasticsearch cluster is all set. In the next section, we will now deploy
[Ralph](https://github.com/openfun/ralph), our LRS.

### Deploy the LRS: Ralph

Ralph is also distributed as a Helm chart. Check out the [Ralph Helm chart README](https://github.com/openfun/ralph/blob/main/src/helm/README.md) to deploy it!

### Deploy the dashboard suite: Warren

Let's create secrets needed for Warren deployment with:
```bash
kubectl create secret generic warren-api-secrets --from-env-file=warren/charts/api/.secret
kubectl create secret generic warren-app-secrets --from-env-file=warren/charts/app/.secret
```

We can now deploy Warren along with its dependencies
using:

```bash
# Fetch dependencies
helm dependency build ./warren

# Install Warren
helm install warren ./warren --values development.yaml --debug --atomic
```

If you want to upgrade your deployment (after a change in a template or a
value), you can upgrade deployed version using:

```bash
helm upgrade --install warren ./warren --values development.yaml --debug --atomic
```
