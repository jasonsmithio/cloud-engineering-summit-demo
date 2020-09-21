# Standing up Serverless with Pulumi and Knative

## Information

[Python SDK Docs](https://www.pulumi.com/docs/reference/pkg/python/pulumi/ "Python SDK Docs")

# NOTE: THIS REQUIRES A GOOGLE CLOUD ACCOUNT

_This tutorial borrows from my [Serverless Eventing](serverlesseventing.com) series. You can find that GitHub repo [here](https://github.com/TheJaySmith/serverless-eventing/tree/master/tutorials/kafka)._

_It also builds off of the [GitHub Repo](https://github.com/metral/cncf-gke-pulumi) from Mike Metral at [Pulumi](Pulumi.com). We did a joint webinar with the [Cloud Native Computing Foundation](cncf.io) that you can find [linked here](https://www.cncf.io/webinars/building-production-ready-services-with-kubernetes-and-serverless-architectures/)._

# SETTING UP

## AlphaVantage

For demos, [AlphaVantage](alphavantage.co "AlphaVantage") is my goto source. They have a free tier that allows around 500 API calls/day and it's easy to sign up. You can get your key [here](https://www.alphavantage.co/support/#api-key "here"). Be sure to save it as we'll need it later.

```bash
gcloud secrets create alpha-vantage-key --replication-policy="automatic"
```

Create a file called `myapikey.txt` and store your AlphaVantage key. Now we will add the API Key to our Secret. 

```bash
gcloud secrets versions add alpha-vantage-key --data-file="/path/to/myapikeytxt"
```

## Variables and Google Cloud

Let's set some system variables such as a `PROJECT_ID` and `BUCKET_ID`. The `PROJECT_ID` should be your Google Cloud Project ID.

```bash
export PROJECT_ID=<YOUR PROJECT ID>
export PROJ_NUMBER=$(gcloud projects list --filter="${PROJECT_ID}" --format="value(PROJECT_NUMBER)")
export ALPHA_VANTAGE_KEY=<YOUR ALPHAVANTAGE API KEY>
```

We will now enable the necessary GCP APIs.

```bash
gcloud services enable --project ${PROJECT_ID} container.googleapis.com \
  secretmanager.googleapis.com\
  cloudkms.googleapis.com \
  storage-api.googleapis.com \
  storage-component.googleapis.com
```

Next we will give GKE access to Secret Manager

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:$PROJ_NUMBER-compute@developer.gserviceaccount.com \
  --role roles/secretmanager.admin
```

And Apply permissions to our cluster.

```bash
kubectl create clusterrolebinding cluster-admin-binding \
  --clusterrole cluster-admin \
  --user $(gcloud config get-value account)
```

## BUILDING OUR INFRASTRUCTURE

Let's now build our application. First, let's make sure that `gcloud` will be properly authenitcated with the `docker` command. If you do not have Docker installed, you can find it [here](https://docs.docker.com/get-docker/ "here").

```bash
gcloud auth configure-docker
```

Next we will pull down our code.

```bash
git clone https://github.com/TheJaySmith/cloud-engineering-summit-demo
cd cloud-engineering-summit-demo
```

### Pulumi with Python: install dependencies

If you plan on using [Python 3](https://www.python.org/downloads/), you can follow these steps.

```bash
cd pulumi-py/
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### Pulumi with Typescript: install dependencies

If you plan on using [TypeScript](https://www.typescriptlang.org/#installation), you can follow these steps.

```bash
cd pulumi-ts/
npm install
```

[![Deploy](https://get.pulumi.com/new/button.svg)](https://app.pulumi.com/new)

## Google Kubernetes Engine (GKE) 

This example provisions a [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine/) cluster, using
infrastructure-as-code, and then deploys a Kubernetes Deployment into it, to test that the cluster is working. This
demonstrates that you can manage both the Kubernetes objects themselves, in addition to underlying cloud infrastructure,
using a single configuration language (in this case, Python), tool, and workflow.

### Prerequisites

Ensure you have [the Pulumi CLI](https://www.pulumi.com/docs/get-started/install/).

We will be deploying to Google Cloud Platform (GCP), so you will need an account. If you don't have an account,
[sign up for free here](https://cloud.google.com/free/). In either case,
[follow the instructions here](https://www.pulumi.com/docs/intro/cloud-providers/gcp/setup/) to connect Pulumi to your GCP account.

This example assumes that you have GCP's `gcloud` CLI on your path. This is installed as part of the
[GCP SDK](https://cloud.google.com/sdk/).

### Running the Example

After cloning this repo, `cd` into it and run these commands. A GKE Kubernetes cluster will appear!

1. Create a new stack, which is an isolated deployment target for this example:

```bash
pulumi stack init dev
```

2. Set the required configuration variables for this program:

```bash
pulumi config set gcp:project [your-gcp-project-here]
pulumi config set gcp:zone us-west1-a # any valid GCP zone here
pulumi config set master_version latest #any valid master version
```

By default, your cluster will have 3 nodes of type `n1-standard-1`. This is configurable, however; for instance
if we'd like to choose 5 nodes of type `n1-standard-2` instead, we can run these commands:

```bash
pulumi config set node_count 5
pulumi config set node_machine_type n1-standard-2
```

This shows how stacks can be configurable in useful ways. You can even change these after provisioning.

1. Deploy everything with the `pulumi up` command. This provisions all the GCP resources necessary, including
   your GKE cluster itself, and then deploys a Kubernetes Deployment running nginx, all in a single gesture:

```bash
pulumi up
```

This will show you a preview, ask for confirmation, and then chug away at provisioning your cluster:

```bash
Updating stack 'gcp-ts-gke-dev'
Performing changes:

        Type                            Name          Plan
    +   pulumi:pulumi:Stack             gcp-py-dev    create
    +   ├─ gcp:container:Cluster        gke-cluster   create
    +   ├─ pulumi:providers:kubernetes  gkeK8s        create
    +   └─ kubernetes:apps:Deployment   canary        create
    +   └─ kubernetes:core:Service      ingress       create

    ---outputs:---
    kubeConfig: "apiVersion: v1\n..."

info: 5 changes updated:
    + 5 resources created
Update duration: 2m07.424737735s
```

After about two minutes, your cluster will be ready, and its config will be printed.

4. From here, you may take this config and use it either in your `~/.kube/config` file, or just by saving it
   locally and plugging it into the `KUBECONFIG` envvar. All of your usual `gcloud` commands will work too, of course.

   For instance:

   ```bash
   $ pulumi stack output kubeconfig > kubeconfig.yaml
   $ KUBECONFIG=./kubeconfig.yaml kubectl get po
   NAME                              READY     STATUS    RESTARTS   AGE
   canary-n7wfhtrp-fdbfd897b-lrm58   1/1       Running   0          58s
   ```

5. At this point, you have a running cluster. Feel free to modify your program, and run `pulumi up` to redeploy changes.
   The Pulumi CLI automatically detects what has changed and makes the minimal edits necessary to accomplish these
   changes. This could be altering the existing chart, adding new GCP or Kubernetes resources, or anything, really.


# Serverless Application

Next we will build our currency app. Let's go to the currency app folder.

```bash
cd app/currency/
```

Let's take a look at the app in the `currency-source.py` file.

```bash
CURR1 = 'USD'
CURR2 = 'JPY'
```

These are the currency values that we will be using. While I have hardcoded 'USD' and 'JPY', you can change this to anything that you want.

```bash
afx = ForeignExchange(key=ALPHAVANTAGE_KEY)

def make_msg(message):
    msg = '{"msg": "%s"}' % (message)
    return msgs


def get_currency():
    data, _ = afx.get_currency_exchange_rate(
            from_currency=CURR1, to_currency=CURR2)
    exrate = data['5. Exchange Rate']
    return exrate


while True:
    headers = {'Content-Type': 'application/cloudevents+json'}
    body = get_currency()
    requests.post(sink_url, data=json.dumps(body), headers=headers)
    time.sleep(30)
```

We first create an AlphaVantage object using our key called `afx`. The `make_msg` function formats the function. The `def_currency` function will use CURR1 and CURR2 and return an exchange rate. The while loop will execute the `def_currency` function, get the exchange rate, and send it to our event sink every 30 seconds. You could make it more or less but I chose '30' as it will give you more time to play with it during the 500 calls/day limit.

Now lets build the containers and push them to [Google Container Registry](https://cloud.google.com/container-registry "Google Container Registry").

```bash
docker build --build-arg PROJECT_ID=${PROJECT_ID} -t gcr.io/${PROJECT_ID}/currency-source:v1  .
docker push gcr.io/${PROJECT_ID}/currency-source:v1
```

### Kafka Producer

Now we will build our `producer-sink`. This application will receive the applications and then push them to Kafka.

```bash
cd ../producer
```

Let's take a look at `kafka-producer.py`

```baash
import os
import json
import logging
import time

from flask import Flask, jsonify, redirect, render_template, request, Response

from kafka import KafkaProducer
from kafka.client import SimpleClient
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer


app = Flask(__name__)

producer = KafkaProducer(
    bootstrap_servers=['my-cluster-kafka-bootstrap.kafka:9092'])


def info(msg):
    app.logger.info(msg)


@app.route('/', methods=['POST'])
def default_route():
    if request.method == 'POST':
        content = request.data.decode('utf-8')
        info(f'Event Display received event: {content}')

        producer.send('finance', bytes(content, encoding='utf-8'))
        return jsonify(hello=str(content))
    else:
        return jsonify('hello world')

if __name__ != '__main__':
    # Redirect Flask logs to Gunicorn logs
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    info('Event Display starting')
else:
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
```

This will receive the events sent by the currency app. This is effectively the `event sink`. It will then send the information to our Kafka Cluster but will also log the outputs so that you can view them in `kubectl logs`.

Now let's build the containers.

```bash
docker build -t gcr.io/${PROJECT_ID}/kafka-producer:v1 .
docker push gcr.io/${PROJECT_ID}/kafka-producer:v1
```

### Event Display

This application takes [CloudEvents](https://cloudevents.io/) and then displays them to the CLI via the Kubernetes logs. We will call this service `event-display`.

```bash
cd ../viewer/
```

Let's turn this application into a container.

```bash
docker build -t gcr.io/${PROJECT_ID}/event-viewer:v1 .
docker push gcr.io/${PROJECT_ID}/event-viewer:v1
```

Great, now it is time to test and deploy.

## Deploy Event Producers

### Setting up Kafka

First we need to ensure that we have our [Kafka Source](https://knative.dev/docs/eventing/samples/kafka/source/) setup. This is an Eventing source provided by Knative Eventing. Let's dive in and look at our Kafka manifests.

```bash
cd ../../manifests/kafka
```

First, we will install a kafka cluster using [Strimzi](strimzi.io). We can treat the cluster like another Kubernetes object thanks to Strimzi.

```bash
kubectl apply -f kafka-cluster.yaml
```

Let's apply the [Kafka Source extension for Eventing version 0.15](https://github.com/knative/eventing-contrib/releases/download/v0.15.0/kafka-source.yaml). You can extend Knative Eventing and c[reate your own](https://knative.dev/docs/eventing/samples/writing-receive-adapter-source/) event sources, but fortunately Kafka's popularity has resulted in one existing out of box.

```bash
kubectl apply -f kafka-source-release.yaml
```

Now we will create a Kafka Topic. Kafka stores rercords in categories called "topics". You can learn more about them [here](https://kafka.apache.org/documentation/#topicconfigs) as they are a key part of Kafka.

For our purposes, we are creating one called 'finance'. Let's go ahead and apply it's manifest.

```bash
kubectl apply -f finance-topic.yaml
```

We are now ready to use Kafka.

### Some Serverless Eventing Fun

First let's check out our config files.

```bash
sed -i '' 's/PROJECT_ID/'${PROJECT_ID}'/g' currency-source.yaml
sed -i '' 's/PROJECT_ID/'${PROJECT_ID}'/g' kafka-producer.yaml
sed -i '' 's/PROJECT_ID/'${PROJECT_ID}'/g' event-viewer.yaml
```

We entered the `config` directory and added our `PROJECT_ID` to the `currency-sourcer.yaml` and `kafka-producer.yaml` files.

`currency-source.yaml` will deploy a [Knative Service](https://knative.dev/docs/serving/services/creating-services/ "Knative Service") for our controller container. This will generate our messages as the **event source**. `kafka-producer.yaml` will deploy a Knative service for our currency-kafka container. This will receive the messages from the controller. We call this the **event si

Lets deploy these. Now they should be deployed in a sequence so give about 10 seconds to each one before you deploy the next.

First we will deploy the binding. This file will tell us to bind our event source (`currency-source`) to our event sink (`currency-kafka`). Lets examine this first.

```bash
apiVersion: sources.knative.dev/v1alpha2
kind: SinkBinding
metadata:
  name: currency-sink-bind
spec:
  subject:
    apiVersion: serving.knative.dev/v1
    kind: Service
    name: currency-controller
  sink:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: currency-kafka
```

Here you can see that we deploy the SinkBinding underthe name `currency-sink-bind`. This will take the "subject" as the event source and the sink as the event sink. For these purposes we are using a Knative Service but [SinkBinding](https://knative.dev/docs/eventing/samples/sinkbinding/ "SinkBinding") does allow for you to use other Kubernetes objects such as datasets.

Now let's deploy.

```bash
kubectl apply -f sink-binding.yaml
```

Next we deploy the currency-kafka service. We want to ensure that our sink is ready to receive before we deploy the source.

```bash
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: kafka-producer
spec:
  template:
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/kafka-producer:v1
        imagePullPolicy: Always
```

This is a standard Knative Service for currency Kafka. Now lets deploy.

```bash
kubectl apply -f kafka-producer.yaml
```

Finally we deploy the currency-controller service. This will start creating events as soon as we deploy. Let's look at the file

```bash
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: currency-source
spec:
  template:
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/currency-source:v1
        imagePullPolicy: Always
```

and deploy...

```bash
kubectl apply -f currency-source.yaml
```

Now let's ensure that everything is running.

```bash
kubectl get pods
```

You should see the `source` and `kafka` service running.

Now let's deploy our `KafkaSource`. This is a custom Eventing source from Knative. It creates a Knative Service that acts as a Kafka consumer and sends the consumed data to an event sink.

Let's take a quick look at `kafka-consumer.yaml`.

```bash
apiVersion: sources.knative.dev/v1alpha1
kind: KafkaSource
metadata:
  name: kafka-consumer
spec:
  consumerGroup: knative-group
  bootstrapServers:
  - my-cluster-kafka-bootstrap.kafka:9092 # note the kafka namespace
  topics:
  - finance
  sink:
    ref:
      apiVersion: serving.knative.dev/v1
      kind: Service
      name: event-viewer
```

Here we are simply saying that Knative Eventing will consume from our Strimzi Kafka cluster uses the 'finance' topic we created earlier. It will then send the data our 'event sink', the 'event-display' service. This service simply logs input to the CLI.

Let's deploy our `kafka-consumer`

```bash
kubectl applty -f kafka-consumer.yaml
```

Now we deploy the `event-viewer`.

```bash
kubectl apply -f event-viewer.yaml
```

## Let's Test

### Try it Out

```bash
kubectl logs --selector='serving.knative.dev/service=event-viewer' -c user-container
```

If done correctly, you should see a new number pop up every 30 seconds like:

```bash
[2020-09-21 16:52:36 +0000] [1] [INFO] Starting gunicorn 19.9.0
[2020-09-21 16:52:36 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2020-09-21 16:52:36 +0000] [1] [INFO] Using worker: threads
[2020-09-21 16:52:36 +0000] [9] [INFO] Booting worker with pid: 9
[2020-09-21 16:52:36 +0000] [9] [INFO] Event Display starting
[2020-09-21 16:52:48 +0000] [9] [INFO] Event Display received event: "104.67000000" ##Our value!
```

## Summarize

Sending data from a source to a single sink may not seem impressive but let's imagine scaling. We want to create sources for every posssible currency exchange and send them to Kafka but you don't want to force write N Kafka connectors for each currency type. You also don't want to write a large monolithic application that handles every possible message type to simplify.

While adopting microservices, you just create event-sources to generate the events then use the SinkBinding to tell the events where to go. In this example, we used a single event-sink but you could further scale it out with [Channels](https://knative.dev/docs/eventing/channels/) and [Brokers](https://knative.dev/docs/eventing/broker-trigger/) which I will explain in a later tutorial.

PLEASE NOTE: This is an example of how to deploy Kafka on Kubernetes and create a streaming application. Realistically, you would want to make a larger Kubernetes cluster for Kafka and consider how you would secure and expose the brokers.

## End

# Cleanup

Once you are done, you can destroy all of the resources, and the stack:

```bash
pulumi destroy
pulumi stack rm
```
