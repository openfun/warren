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

Ralph is also distributed as a Helm chart that can be deployed with a single
line of code:

```bash
helm install \
    --values charts/ralph/values.yaml \
    --set envSecrets.RALPH_BACKENDS__DATABASE__ES__HOSTS=https://elastic:"${ELASTIC_PASSWORD}"@data-lake-es-http:9200 \
    lrs oci://registry-1.docker.io/openfuncharts/ralph
```

One can check if the server is running by opening a network tunnel to the
service using the `port-forward` sub-command:


```bash
kubectl port-forward svc/lrs-ralph 8080:8080
```

And then send a request to the server using this tunnel:

```bash
curl --user admin:password localhost:8080/whoami
```

We expect a valid JSON response stating about the user you are using for this
request.

If everything went well, we can send 22k xAPI statements to the LRS using:

```bash
gunzip -c ../../data/statements.jsonl.gz | \
  sed "s/@timestamp/timestamp/g" | \
  jq -s . | \
  curl -Lk \
    --user admin:password \
    -X POST \
    -H "Content-Type: application/json" \
    http://localhost:8080/xAPI/statements/ -d @-
```

### Deploy the dashboard suite: Warren

Now that the LRS is running, we can deploy warren along with its dependencies
using:

```bash
# Fetch dependencies
cd warren && helm dependency build

# Deploy postgresql for Warren `app` service (Django)
helm install warren ./warren --values development.yaml --debug --atomic
```

If you want to upgrade your deployment (after a change in a template or a
value), you can upgrade deployed version using:

```bash
# Deploy postgresql for Warren `app` service (Django)
helm upgrade --install warren ./warren --values development.yaml --debug --atomic
```
