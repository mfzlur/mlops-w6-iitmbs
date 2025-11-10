# IRIS Flower Classification API - Continuous Deployment with GitHub Actions

A production-ready machine learning API that classifies IRIS flowers using an ensemble model (SVM + Gradient Boosting). Fully automated CI/CD pipeline with GitHub Actions, Docker containerization, and Kubernetes deployment on Google Cloud.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Local Development](#local-development)
- [CI/CD Pipeline](#cicd-pipeline)
- [API Endpoints](#api-endpoints)
- [Model Details](#model-details)
- [Troubleshooting](#troubleshooting)

## 🎯 Project Overview

This project demonstrates modern DevOps practices by building an automated deployment pipeline for a machine learning model:

- **ML Model**: Advanced ensemble classifier combining SVM (with GridSearchCV hyperparameter tuning) and Gradient Boosting
- **API Framework**: FastAPI with automatic interactive documentation
- **Containerization**: Docker for consistent deployment across environments
- **Orchestration**: Kubernetes (GKE) for scalable container management
- **CI/CD**: GitHub Actions for fully automated build, test, and deploy workflow
- **Registry**: Google Artifact Registry for secure image storage

### Key Features

✅ Automated builds and deployments on every git push  
✅ High-accuracy ensemble model (~97% on IRIS dataset)  
✅ RESTful API with automatic Swagger documentation  
✅ Health checks and readiness probes  
✅ Horizontal scaling with multiple replicas  
✅ Confidence scores and probability distribution for predictions  
✅ Production-ready error handling and validation  

## 🏗️ Architecture

### Kubernetes Pod vs Docker Container

| **Aspect** | **Docker Container** | **Kubernetes Pod** |
|---|---|---|
| **Definition** | Isolated package containing application code, runtime, and dependencies | Smallest deployable unit in Kubernetes; wraps one or more containers |
| **Networking** | Each container has its own network namespace; requires port mapping | All containers in a pod share the same network namespace; can communicate via localhost |
| **Storage** | Ephemeral storage lost when container terminates | Can use persistent volumes; data survives container restarts |
| **Lifecycle** | Managed by Docker runtime (create, start, restart, stop) | Managed by Kubernetes control plane (Pending → Running → Succeeded/Failed) |
| **Isolation** | Isolated from other containers at runtime level | Pod is isolated from other pods; internal containers share network IP and ports |

**Simple Analogy**: A Docker container is a **packaged shipping box**, while a Pod is a **shelf in a warehouse** that holds one or more boxes and provides shared infrastructure (network cable, power).

### Deployment Flow

```
Developer Push to GitHub (main branch)
              ↓
GitHub Actions Workflow Triggered
              ↓
┌─────────────────────────────────────┐
│ BUILD PHASE                         │
│ - Checkout code from GitHub         │
│ - Build Docker image from Dockerfile│
│ - Tag with commit SHA               │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ PUSH PHASE                          │
│ - Authenticate to Google Cloud      │
│ - Push image to Artifact Registry   │
│ - Tag: :latest and :commit-sha      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ DEPLOY PHASE                        │
│ - Get credentials to GKE cluster    │
│ - Update deployment with new image  │
│ - kubectl set image triggers        │
│ - Rolling update to new pods        │
└─────────────────────────────────────┘
              ↓
Kubernetes Pulls Image and Creates Pods
              ↓
IRIS API Running in Production ✅
```

## 📦 Prerequisites

### GCP Setup Required

1. **GCP Project** with billing enabled
2. **Enable these APIs:**
   - Kubernetes Engine API
   - Artifact Registry API
   - Container Registry API

3. **GKE Cluster** created in your project
4. **Service Account** with proper IAM roles
5. **GitHub Secrets** configured with credentials

### Local Development Tools

- Python 3.10+
- Docker installed locally
- kubectl installed
- gcloud CLI installed
- Git

## 📁 Project Structure

```
mlops-w6-iitmbs/
├── .github/
│   └── workflows/
│       └── deploy-gke.yml          # GitHub Actions CI/CD workflow
├── main.py                         # FastAPI application
├── train_model.py                  # Model training script
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container build instructions
├── deployment.yaml                 # Kubernetes deployment manifest
├── README.md                       # This file
└── .gitignore                      # Exclude model files from git
```

### File Descriptions

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application with prediction endpoints and health checks |
| `train_model.py` | Trains ensemble model with GridSearchCV, saves to model.pkl and scaler.pkl |
| `requirements.txt` | Python package dependencies (FastAPI, scikit-learn, XGBoost, etc.) |
| `Dockerfile` | Container image definition; trains model on build and runs FastAPI |
| `deployment.yaml` | Kubernetes manifest defining Service and Deployment for GKE |
| `deploy-gke.yml` | GitHub Actions workflow orchestrating build → push → deploy |

## 🚀 Setup Instructions

### Step 1: GCP Configuration

```bash
# Set your GCP project
export PROJECT_ID="your-gcp-project-id"
export ZONE="us-central1-a"
export CLUSTER_NAME="iris-cluster"

# Login to GCP
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable containerregistry.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create GKE cluster (this takes ~5-10 minutes)
gcloud container clusters create $CLUSTER_NAME \
  --zone $ZONE \
  --num-nodes 2 \
  --machine-type n1-standard-2

# Create Docker registry in Artifact Registry
gcloud artifacts repositories create iris-repo \
  --repository-format=docker \
  --location=us-central1

# Create service account for GitHub
gcloud iam service-accounts create github-deployment-sa \
  --display-name="GitHub Deployment Service Account"

# Grant roles to service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:github-deployment-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role=roles/container.admin

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:github-deployment-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role=roles/storage.admin

# Create and export service account key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-deployment-sa@${PROJECT_ID}.iam.gserviceaccount.com

# Convert to base64 for GitHub secret
export GKE_SA_KEY=$(cat key.json | base64)
echo $GKE_SA_KEY
```

### Step 2: GitHub Configuration

1. **Create Repository**
   - Go to GitHub.com → New Repository
   - Name: `iris-api`
   - Clone to local machine: `git clone https://github.com/YOUR_USERNAME/iris-api.git`

2. **Add GitHub Secrets**
   - Repository → Settings → Secrets and variables → Actions
   - Add secret `GKE_PROJECT` = your GCP project ID
   - Add secret `GKE_SA_KEY` = the base64 key from Step 1

3. **Update Workflow File**
   - Edit `.github/workflows/deploy-gke.yml`
   - Replace `YOUR_PROJECT_ID` with your actual GCP project ID

4. **Update Deployment Manifest**
   - Edit `deployment.yaml`
   - Replace `YOUR_PROJECT_ID` with your actual GCP project ID

### Step 3: Local Repository Setup

```bash
# Create project structure
mkdir -p .github/workflows

# Copy all provided files into repository:
# - main.py
# - train_model.py
# - requirements.txt
# - Dockerfile
# - deployment.yaml
# - .github/workflows/deploy-gke.yml

# Create .gitignore
cat > .gitignore << EOF
model.pkl
scaler.pkl
__pycache__/
*.pyc
.env
*.egg-info/
dist/
build/
EOF

# Commit and push
git add .
git commit -m "Initial setup: IRIS API with FastAPI, ensemble model, and GKE deployment"
git push origin main
```

## 💻 Local Development

### Train and Test Model Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Train the model (generates model.pkl and scaler.pkl)
python train_model.py

# Output will show:
# - SVM hyperparameter tuning results
# - Model accuracy (~97%)
# - Classification report per species
# - Model saved to model.pkl
# - Scaler saved to scaler.pkl
```

### Run FastAPI Locally

```bash
# Start FastAPI development server
uvicorn main:app --reload

# Output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get model info
curl http://localhost:8000/model-info

# Make prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }'

# Response:
# {
#   "predicted_species": "setosa",
#   "confidence": 0.98,
#   "probabilities": {
#     "setosa": 0.98,
#     "versicolor": 0.015,
#     "virginica": 0.005
#   },
#   "feature_names": [...],
#   "model_type": "Ensemble (SVM + Gradient Boosting)"
# }
```

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Test Docker Locally

```bash
# Build Docker image
docker build -t iris-api:test .

# Run container
docker run -p 8000:8000 iris-api:test

# Test: curl http://localhost:8000/health
```

## 🔄 CI/CD Pipeline

### How It Works

**Trigger**: Push to `main` branch

**Workflow Steps**:

1. **Checkout**: Clone repository code
2. **Authenticate**: Setup Google Cloud credentials
3. **Build**: Create Docker image with tag `us-central1-docker.pkg.dev/PROJECT_ID/iris-repo/iris-api:COMMIT_SHA`
4. **Push**: Upload image to Google Artifact Registry
5. **Deploy**: Update GKE deployment to use new image
6. **Verify**: Check rollout status and display running services

### Monitoring Pipeline

1. Go to GitHub repository → **Actions** tab
2. Click on workflow run to see detailed logs
3. Each step shows stdout/stderr output
4. Failed steps include error messages for debugging

### Example Workflow Execution

```
✅ Checkout Code (2s)
✅ Authenticate to Google Cloud (5s)
✅ Setup Cloud SDK (8s)
✅ Configure Docker for Artifact Registry (3s)
✅ Get GKE Credentials (4s)
✅ Build Docker Image (45s)
✅ Push to Artifact Registry (12s)
✅ Deploy to GKE (25s)
✅ Show Services (3s)

Total: ~2 minutes
```

## 🔌 API Endpoints

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_type": "Ensemble (SVM + Gradient Boosting)"
}
```

### GET /model-info

Get model and dataset information.

**Response:**
```json
{
  "model_type": "Ensemble (SVM + Gradient Boosting)",
  "iris_species": ["setosa", "versicolor", "virginica"],
  "features": [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)"
  ],
  "description": "Advanced ensemble model..."
}
```

### POST /predict

Predict IRIS species from flower measurements.

**Request:**
```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```

**Response:**
```json
{
  "predicted_species": "setosa",
  "confidence": 0.98,
  "probabilities": {
    "setosa": 0.98,
    "versicolor": 0.015,
    "virginica": 0.005
  },
  "feature_names": ["sepal length (cm)", "sepal width (cm)", "petal length (cm)", "petal width (cm)"],
  "model_type": "Ensemble (SVM + Gradient Boosting)"
}
```

### GET /

Root endpoint with links to documentation.

## 🧠 Model Details

### Model Architecture

**Ensemble Voting Classifier combining:**

1. **Support Vector Machine (SVM)**
   - Kernel: RBF (Radial Basis Function) or Polynomial
   - Hyperparameters tuned via GridSearchCV over 5-fold cross-validation
   - C values tested: [0.1, 1, 10, 100]
   - Gamma values tested: ['scale', 'auto', 0.001, 0.01]
   - ~97% accuracy on test set

2. **Gradient Boosting Classifier**
   - 100 estimators
   - Learning rate: 0.1
   - Max depth: 3
   - Captures non-linear relationships

**Voting Strategy**: Soft voting (average predicted probabilities)

### Data Preprocessing

- **Feature Scaling**: StandardScaler normalizes all features (critical for SVM)
- **Train/Test Split**: 80/20 split with stratification (balanced class distribution)
- **Dataset**: UCI Machine Learning Repository IRIS dataset (150 samples, 4 features, 3 classes)

### Performance Metrics

```
Accuracy: ~97%
Precision per class: ~96-99%
Recall per class: ~96-100%
F1-Score: ~97%
```

## 🔍 Verification Checklist

After deployment, verify everything works:

```bash
# Get GKE cluster credentials (if not already done)
gcloud container clusters get-credentials iris-cluster --zone us-central1-a

# Check all Kubernetes resources
kubectl get all

# View deployed pods
kubectl get pods

# View services (get external IP)
kubectl get services

# Check deployment status
kubectl describe deployment iris-api-deployment

# View logs from a pod
kubectl logs <POD_NAME>

# Test API from pod
kubectl exec -it <POD_NAME> -- curl http://localhost:8000/health

# Port-forward for local testing
kubectl port-forward service/iris-api-service 8080:80
# Then: curl http://localhost:8080/health
```

## 🐛 Troubleshooting

### Pod stuck in ImagePullBackOff

**Issue**: Pod can't pull image from Artifact Registry

**Solution**:
```bash
# Check pod status
kubectl describe pod <POD_NAME>

# Verify service account has permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:github-deployment-sa*"

# Manually authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Workflow fails at "Deploy to GKE" step

**Solution**:
```bash
# Check credentials
echo $GKE_SA_KEY | base64 -d | jq .

# Verify service account has container.admin role
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:*github-deployment-sa* AND bindings.role:*container.admin*"
```

### Model predictions are wrong

**Issue**: Ensemble model making incorrect predictions

**Check**:
```bash
# Run local prediction test
python -c "
import pickle
import numpy as np

# Load model and scaler
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)
with open('scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# Test with known IRIS sample
features = np.array([[5.1, 3.5, 1.4, 0.2]])  # Setosa
features_scaled = scaler.transform(features)
pred = model.predict(features_scaled)
print(f'Prediction: {pred}')  # Should be [0] for Setosa
"
```

### Can't connect to GKE cluster

**Solution**:
```bash
# Update kubeconfig
gcloud container clusters get-credentials iris-cluster \
  --zone us-central1-a \
  --project $PROJECT_ID

# Verify connection
kubectl cluster-info
```

## 📚 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Kubernetes Official Docs](https://kubernetes.io/docs)
- [Google Kubernetes Engine Docs](https://cloud.google.com/kubernetes-engine/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com)
- [scikit-learn Ensemble Methods](https://scikit-learn.org/stable/modules/ensemble.html)

## 📝 Notes

- Model files (`model.pkl`, `scaler.pkl`) are generated during Docker build and NOT committed to git
- Each deployment creates new Pods; old Pods are gracefully terminated
- Liveness probe checks `/health` every 10s; pod restarts if unhealthy for 30s+
- Readiness probe checks `/health` every 5s; pod removed from load balancer if not ready
- Service uses LoadBalancer type; gets external IP to access API from internet

## ✅ Assignment Completion Checklist

- [ ] GCP project created with Kubernetes Engine enabled
- [ ] GKE cluster created
- [ ] Service account created and roles assigned
- [ ] GitHub repository created
- [ ] GitHub secrets configured (GKE_PROJECT, GKE_SA_KEY)
- [ ] All files created (main.py, train_model.py, Dockerfile, deployment.yaml, workflow)
- [ ] Workflow file updated with correct PROJECT_ID
- [ ] Deployment manifest updated with correct PROJECT_ID
- [ ] First push to main triggered GitHub Actions
- [ ] Workflow successfully completed (✅ all steps)
- [ ] Pods are running in GKE (kubectl get pods shows Running)
- [ ] API is accessible via service LoadBalancer IP
- [ ] Prediction endpoint returns correct results
- [ ] Model can be described (Pod vs Container differences explained)

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review GitHub Actions logs for detailed error messages
3. Verify GCP service account permissions
4. Test API locally before deployment
5. Check kubectl logs from deployed pods

---

**Created**: November 2025  
**Framework**: FastAPI  
**Model**: Ensemble (SVM + Gradient Boosting)  
**Deployment**: Google Kubernetes Engine  
**CI/CD**: GitHub Actions
