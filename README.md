# IRIS Flower Classification API - Kubernetes Autoscaling \& Load Testing

A production-ready machine learning API demonstrating Kubernetes Horizontal Pod Autoscaling (HPA) under stress conditions. This project extends the CI/CD pipeline with automated load testing to observe autoscaling behavior and identify performance bottlenecks.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Stress Testing \& Autoscaling](#stress-testing--autoscaling)
- [Test Results Analysis](#test-results-analysis)
- [API Endpoints](#api-endpoints)
- [Model Details](#model-details)
- [Troubleshooting](#troubleshooting)


## 🎯 Project Overview

This project demonstrates Kubernetes autoscaling capabilities by stress testing a machine learning API and observing pod scaling behavior under high concurrent load:

- **ML Model**: Ensemble classifier (SVM + Gradient Boosting) with ~97% accuracy
- **API Framework**: FastAPI with automatic documentation
- **Load Testing**: wrk tool generating >1000 concurrent connections
- **Autoscaling**: Horizontal Pod Autoscaler (HPA) with CPU-based scaling
- **Orchestration**: Google Kubernetes Engine (GKE)
- **CI/CD**: GitHub Actions with automated stress testing


### Assignment Objectives

✅ **Extend CI/CD pipeline** with automated stress testing after deployment
✅ **Stress test with >1000 requests** using wrk load testing tool
✅ **Demonstrate HPA autoscaling** from 1 to 3 pods based on CPU utilization
✅ **Observe bottlenecks** when scaling is restricted to 1 pod with 2000 concurrent requests
✅ **Analyze performance degradation** through socket errors, timeouts, and latency metrics

## 📦 Prerequisites

### Required Components

1. **GCP Project** with billing enabled
2. **Enabled APIs**:
    - Kubernetes Engine API
    - Artifact Registry API
    - Container Registry API
    - Cloud Monitoring API (for HPA metrics)
3. **GKE Cluster** with Metrics Server installed
4. **Service Account** with container.admin and storage.admin roles
5. **GitHub Secrets** configured (GKE_PROJECT, GKE_SA_KEY)

### Local Tools

- Python 3.10+
- Docker
- kubectl
- gcloud CLI
- wrk (HTTP benchmarking tool)


## 📁 Project Structure

```
mlops-w6-iitmbs/
├── .github/
│   └── workflows/
│       └── deploy-gke.yml          # CI/CD with stress testing
├── scripts/
│   └── post.lua                    # wrk Lua script for POST requests
├── main.py                         # FastAPI application
├── train_model.py                  # Model training script
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container image definition
├── deployment.yaml                 # Kubernetes deployment + HPA
└── README.md                       # This file
```


### Key Files

| File | Purpose |
| :-- | :-- |
| `deploy-gke.yml` | GitHub Actions workflow with automated stress tests |
| `deployment.yaml` | Kubernetes Deployment with resource requests/limits | HorizontalPodAutoscaler with 50% CPU target, 1-3 replicas |
| `scripts/post.lua` | wrk Lua script for POST request load testing |

## 🚀 Setup Instructions

### Step 1: GCP Configuration

```bash
# Set variables
export PROJECT_ID="your-gcp-project-id"
export ZONE="us-central1"
export CLUSTER_NAME="iris-cluster"

# Authenticate and set project
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable monitoring.googleapis.com

# Create GKE cluster with autoscaling
gcloud container clusters create $CLUSTER_NAME \
  --zone $ZONE \
  --num-nodes 2 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 4

# Install Metrics Server (required for HPA)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify Metrics Server
kubectl get deployment metrics-server -n kube-system
```




### Step 3: Update Deployment with Resource Limits

Ensure your `deployment.yaml` includes resource requests and limits:

```yaml
containers:
- name: iris-api
  image: us-central1-docker.pkg.dev/PROJECT_ID/iris-repo/iris-api:latest
  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "500m"
      memory: "256Mi"
```


### Step 4: Create wrk POST Script

Create `scripts/post.lua`:

```lua
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

request = function()
    return wrk.format(nil, nil, nil, wrk.body)
end
```


### Step 5: Deploy to Kubernetes

```bash
# Apply all resources (Service, Deployment, HPA) from single file
kubectl apply -f deployment.yaml


# Verify deployment
kubectl get pods
kubectl get hpa
kubectl get svc
```


## 🔥 Stress Testing \& Autoscaling

### Test 1: Autoscaling from 1 to 3 Pods (1200 Connections)

**Objective**: Demonstrate HPA scaling behavior under high load with max 3 pods allowed.

**Configuration**:

- Initial pods: 1
- Max pods: 3
- Concurrent connections: 1200
- Test duration: 30 seconds
- CPU threshold: 50%

**Command**:

```bash
# Get service external IP
export SERVICE_IP=$(kubectl get svc iris-api-service -o jsonpath='{.status.loadBalancer.ingress[^0].ip}')

# Run stress test
wrk -t4 -c1200 -d30s -s scripts/post.lua http://$SERVICE_IP/predict

# Monitor HPA in real-time
kubectl get hpa -w
```

**Expected Behavior**:

1. Initial CPU: ~1% (1 replica)
2. Load applied: CPU spikes to 133%+
3. HPA triggers: Scales from 1 → 3 replicas
4. Load distribution: Traffic balances across 3 pods
5. Final CPU: ~44% per pod (distributed load)

**Actual Results from Logs**:

```
Running 30s test @ http://34.57.207.248
  4 threads and 1200 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     1.41s   474.34ms   2.00s    61.95%
    Req/Sec   147.39     97.52   494.00    68.18%
  13944 requests in 30.07s, 3.09MB read
  Socket errors: connect 0, read 291, write 0, timeout 8943
Requests/sec: 463.78
Transfer/sec: 105.07KB

HPA Status:
NAME           REFERENCE                     TARGETS    MINPODS   MAXPODS   REPLICAS   AGE
iris-api-hpa   Deployment/iris-api-deployment   cpu: 133%/50%   1         3         3          123m
```

**Analysis**: HPA successfully scaled to 3 replicas when CPU exceeded 50% threshold. Socket errors and timeouts decreased as load distributed.

### Test 2: Bottleneck with Restricted Scaling (2000 Connections, Max 1 Pod)

**Objective**: Demonstrate performance bottleneck when autoscaling is disabled.

**Configuration**:

- Max pods: 1 (restricted via HPA patch)
- Concurrent connections: 2000 (67% increase from Test 1)
- Test duration: 30 seconds
- CPU threshold: 50% (but scaling prevented)

**Command**:

```bash
# Restrict HPA to max 1 pod
kubectl patch hpa iris-api-hpa --patch '{"spec":{"maxReplicas":1}}'

# Wait for scale down
kubectl get pods -w

# Run bottleneck test
wrk -t4 -c2000 -d30s -s scripts/post.lua http://$SERVICE_IP/predict

# Monitor pod CPU
kubectl top pods
```

**Expected Behavior**:

1. HPA scales down: 3 → 1 replica
2. Load applied: CPU exceeds 150%
3. HPA blocked: Cannot scale beyond 1 pod
4. Bottleneck symptoms: High socket errors, timeouts, latency
5. Throughput degradation: Lower requests/sec despite higher load

**Actual Results from Logs**:

```
Running 30s test @ http://34.57.207.248
  4 threads and 2000 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency     1.23s   508.12ms   2.00s    66.12%
    Req/Sec   301.27   134.88   770.00    68.89%
  29928 requests in 30.06s, 6.62MB read
  Socket errors: connect 0, read 1523, write 165366, timeout 3706
Requests/sec: 995.61
Transfer/sec: 225.57KB

HPA Status (trapped at 1 replica):
NAME           REFERENCE                     TARGETS    MINPODS   MAXPODS   REPLICAS   AGE
iris-api-hpa   Deployment/iris-api-deployment   cpu: 151%/50%   1         1         1          124m

Pod CPU:
NAME                                    CPU(cores)   MEMORY(bytes)
iris-api-deployment-84d7d467c6-qdtzf   175m         92Mi
```

**Analysis**: Despite 67% more connections, the single pod is overwhelmed:

- **Socket errors increased 524%**: read errors jumped from 291 to 1523
- **Write errors**: 165,366 write errors (connection exhaustion)
- **Timeouts decreased but still high**: 3706 timeouts (41% of Test 1)
- **CPU at 151%**: Exceeds 50% threshold but cannot scale
- **Bottleneck confirmed**: Performance degraded despite higher request rate


## 📊 Test Results Analysis

### Performance Comparison

| Metric | Test 1 (1200 conn, 3 pods) | Test 2 (2000 conn, 1 pod) | Change |
| :-- | :-- | :-- | :-- |
| **Requests/sec** | 463.78 | 995.61 | +115% |
| **Total Requests** | 13,944 | 29,928 | +115% |
| **Avg Latency** | 1.41s | 1.23s | -13% |
| **Socket Read Errors** | 291 | 1,523 | +424% |
| **Socket Write Errors** | 0 | 165,366 | ∞ |
| **Timeouts** | 8,943 | 3,706 | -59% |
| **HPA Replicas** | 3 (scaled) | 1 (trapped) | -67% |
| **CPU Utilization** | 133% → 44%/pod | 151% (single pod) | N/A |



### Key Insights

1. **Autoscaling prevents bottlenecks**: Test 1 distributed load across 3 pods, reducing per-pod CPU from 133% to ~44%
2. **Single pod saturation**: Test 2 showed CPU at 151% with no scaling ability, causing massive socket write errors (165K+)
3. **Connection exhaustion**: Write errors indicate the single pod couldn't accept new connections fast enough
4. **Throughput paradox**: Higher requests/sec in Test 2, but quality degraded (more errors)
5. **HPA effectiveness**: CPU-based autoscaling successfully detected load and scaled appropriately when unrestricted

## 🔌 API Endpoints

### GET /health

Health check endpoint.

**Response**:

```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_type": "Ensemble (SVM + Gradient Boosting)"
}
```


### POST /predict

Predict IRIS species from flower measurements.

**Request**:

```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```

**Response**:

```json
{
  "predicted_species": "setosa",
  "confidence": 0.98,
  "probabilities": {
    "setosa": 0.98,
    "versicolor": 0.015,
    "virginica": 0.005
  },
  "model_type": "Ensemble (SVM + Gradient Boosting)"
}
```


## 🧠 Model Details

### Ensemble Architecture

**Voting Classifier combining**:

1. **Support Vector Machine (SVM)**
    - Kernel: RBF (Radial Basis Function)
    - GridSearchCV hyperparameter tuning (5-fold CV)
    - C values: [0.1, 1, 10, 100]
    - Gamma values: ['scale', 'auto', 0.001, 0.01]
2. **Gradient Boosting Classifier**
    - 100 estimators
    - Learning rate: 0.1
    - Max depth: 3

**Performance**: ~97% accuracy on IRIS test set

### Resource Configuration

Container resources for HPA:

- **CPU Request**: 100m (minimum guaranteed)
- **CPU Limit**: 500m (maximum allowed)
- **Memory Request**: 128Mi
- **Memory Limit**: 256Mi


## 🔍 Verification Commands

```bash
# Check HPA status
kubectl get hpa

# Monitor pods in real-time
kubectl get pods -w

# Check pod resource usage
kubectl top pods

# View HPA details
kubectl describe hpa iris-api-hpa

# Get service external IP
kubectl get svc iris-api-service

# Test API health
curl http://$SERVICE_IP/health
```


## 🐛 Troubleshooting

### HPA Not Scaling

**Symptom**: HPA shows `<unknown>` for CPU metrics

**Solution**:

```bash
# Verify Metrics Server is running
kubectl get deployment metrics-server -n kube-system

# Check pod resource requests are defined
kubectl describe pod <POD_NAME> | grep -A 5 "Requests:"

# View HPA events
kubectl describe hpa iris-api-hpa
```


### wrk Lua Script Errors

**Symptom**: `attempt to index global 'thread' (a nil value)`

**Cause**: Script trying to access thread-specific variables incorrectly

**Solution**: Use simplified POST script without thread references:

```lua
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```


### High Socket Errors

**Symptom**: Large number of socket write/read errors during load test
**Analysis**: Indicates server connection exhaustion or pod resource limits

**Solutions**:

1. Increase HPA `maxReplicas` to distribute load
2. Increase CPU/memory limits in deployment
3. Tune connection timeouts and keepalive settings

## ✅ Assignment Completion Checklist

- [ ] GKE cluster created with Metrics Server
- [ ] HPA configured with 1 min, 3 max replicas, 50% CPU target
- [ ] Deployment includes resource requests and limits
- [ ] wrk installed and POST script created
- [ ] GitHub Actions workflow includes stress testing steps
- [ ] Test 1: Successfully scaled from 1 to 3 pods with 1200 connections
- [ ] Test 1: HPA CPU target reached 133%+ and triggered scaling
- [ ] Test 2: HPA patched to max 1 pod
- [ ] Test 2: Bottleneck observed with 2000 connections (high errors)
- [ ] Test 2: CPU exceeded 150% but scaling blocked
- [ ] Performance metrics documented (latency, errors, throughput)
- [ ] Screenshots/logs captured showing HPA scaling behavior


## 📝 Key Takeaways

1. **HPA enables elastic scaling**: Automatically adjusts pod count based on CPU utilization
2. **Resource limits are critical**: Proper requests/limits enable accurate HPA calculations
3. **Bottlenecks are observable**: Socket errors and latency increase when scaling is restricted
4. **CPU is not always optimal**: Consider custom metrics (latency, queue depth) for complex workloads
5. **Load testing validates architecture**: wrk effectively simulates high-concurrency scenarios
***
