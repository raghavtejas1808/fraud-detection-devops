# Fraud Detection DevOps Pipeline — Project Report

---

## 1. Introduction

### 1.1 Project Overview
This project implements a **real-time financial fraud detection system** built with modern MLOps and DevSecOps practices. It combines a machine learning model (Isolation Forest) served via a REST API with a complete CI/CD pipeline, container orchestration, centralized logging, and secrets management.

### 1.2 Objective
- Develop a machine learning-based fraud detection API capable of scoring financial transactions in real-time
- Implement an end-to-end DevOps pipeline covering continuous integration, continuous deployment, monitoring, and security
- Demonstrate industry-standard practices including containerization, orchestration, infrastructure-as-code, and centralized log management

### 1.3 Problem Statement
Financial fraud causes billions in losses annually. Manual fraud detection is slow and error-prone. This project addresses the need for an automated, scalable, real-time fraud scoring system backed by robust DevOps infrastructure for reliable production deployment.

---

## 2. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Application | Python 3.11, FastAPI, Pydantic | REST API framework with request validation |
| Machine Learning | scikit-learn (Isolation Forest), joblib, NumPy, Pandas | Anomaly detection model training and inference |
| CI/CD | Jenkins, GitHub Webhooks | Automated build, test, and deployment pipeline |
| Containerization | Docker, Docker Compose | Application packaging and multi-service orchestration |
| Configuration Management | Ansible (with Roles) | Automated server provisioning and deployment |
| Orchestration | Kubernetes, HPA | Container orchestration with auto-scaling |
| Secrets Management | HashiCorp Vault | Secure storage of credentials and API keys |
| Monitoring & Logging | ELK Stack (Elasticsearch, Logstash, Kibana) | Centralized log aggregation and visualization |
| Testing | pytest, FastAPI TestClient, httpx | Unit and integration testing |

---

## 3. Project Structure

```
fraud-detection-devops/
├── app/                        # Application layer
│   ├── main.py                 # FastAPI app with /predict, /health endpoints
│   ├── train.py                # Isolation Forest model training script
│   ├── simulate.py             # Live transaction simulator
│   ├── test_main.py            # Unit tests (pytest)
│   ├── Dockerfile              # Container image definition
│   └── requirements.txt        # Python dependencies
├── jenkins/                    # CI/CD pipeline
│   └── Jenkinsfile             # 7-stage declarative pipeline
├── docker/                     # Docker Compose stack
│   └── docker-compose.yml      # 5 services: API, ELK, Vault
├── ansible/                    # Configuration management
│   ├── site.yml                # Main playbook
│   ├── inventory.ini           # Host inventory
│   └── roles/
│       ├── app/main.yml        # Deploy fraud-api container
│       ├── monitoring/main.yml # Deploy ELK stack
│       └── k8s/main.yml        # Apply Kubernetes manifests
├── k8s/                        # Kubernetes manifests
│   ├── deployment.yaml         # RollingUpdate + health probes
│   ├── service.yaml            # LoadBalancer service
│   └── hpa.yaml                # Horizontal Pod Autoscaler (2–10 pods)
├── elk/                        # Log pipeline
│   └── logstash.conf           # JSON log parsing → Elasticsearch
└── vault/                      # Secrets
    └── vault-policy.hcl        # Vault access control policy
```

---

## 4. Application Design

### 4.1 Machine Learning Model

**Algorithm:** Isolation Forest (unsupervised anomaly detection)

The model is trained on the Kaggle Sparkov fraud detection dataset using `train.py`. It performs the following feature engineering:

| Feature | Derivation |
|---------|-----------|
| `amt` | Transaction amount (directly from dataset) |
| `category_enc` | Merchant category encoded via `LabelEncoder` |
| `hour` | Hour of day extracted from transaction timestamp |
| `distance` | Euclidean distance between cardholder and merchant location (converted to km) |
| `is_fraud` | Ground truth label from dataset |

**Hyperparameters:**
- `n_estimators = 100` (number of trees)
- `contamination = 0.01` (expected fraction of anomalies)
- `random_state = 42` (reproducibility)

The trained model is serialized via `joblib` as `fraud_model.pkl`.

### 4.2 API Endpoints

The FastAPI application (`main.py`) exposes three endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint — returns API status message |
| `/predict` | POST | Accepts transaction data, returns fraud prediction |
| `/health` | GET | Health check — returns `{"status": "ok"}` |

**Request Schema (`/predict`):**

```json
{
    "amount": 4500.0,
    "merchant_category": "online_retail",
    "hour_of_day": 2,
    "distance_from_home_km": 1200.0,
    "is_foreign_transaction": 1
}
```

**Response Schema:**

```json
{
    "is_fraud": true,
    "fraud_score": -0.5,
    "merchant_category": "online_retail",
    "amount": 4500.0
}
```

The `merchant_category` field maps to encoded values: `grocery (0)`, `online_retail (1)`, `gas (2)`, `entertainment (3)`, `travel (4)`, `other (5)`.

### 4.3 Transaction Simulator

`simulate.py` continuously generates random transactions and sends them to the API:
- **Normal transactions (90%):** Low amounts ($5–$300), daytime hours, short distances, domestic
- **Fraudulent transactions (10%):** High amounts ($800–$5000), late-night hours, long distances, foreign

---

## 5. Containerization (Docker)

### 5.1 Dockerfile

The application is containerized using a lightweight `python:3.11-slim` base image:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 Docker Compose

The `docker-compose.yml` orchestrates 5 services in a single stack:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `fraud-api` | Built from `app/Dockerfile` | 8000 | Fraud detection API |
| `elasticsearch` | `elasticsearch:8.12.0` | 9200 | Log storage and search engine |
| `logstash` | `logstash:8.12.0` | 5044 | Log ingestion and parsing |
| `kibana` | `kibana:8.12.0` | 5601 | Log visualization dashboard |
| `vault` | `vault:1.16` | 8200 | Secrets management |

**Shared Volumes:**
- `app_logs` — shared between `fraud-api` (write) and `logstash` (read-only) for log forwarding
- `es_data` — persistent Elasticsearch data

**Service Dependencies:**
- `fraud-api` depends on `elasticsearch`
- `logstash` depends on `elasticsearch` and `fraud-api`
- `kibana` depends on `elasticsearch`

---

## 6. CI/CD Pipeline (Jenkins)

### 6.1 Pipeline Overview

The Jenkins pipeline is defined as a declarative `Jenkinsfile` and triggers automatically on every push to the `main` branch via GitHub Webhooks.

### 6.2 Pipeline Stages

```
┌──────────┐   ┌───────────────┐   ┌────────────────────┐   ┌───────────┐
│ Checkout │──▶│ Fetch Secrets │──▶│ Install Dependencies│──▶│ Run Tests │
└──────────┘   │  (from Vault) │   └────────────────────┘   └─────┬─────┘
               └───────────────┘                                   │
                                                                   ▼
┌─────────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
│ Deploy with Ansible │◀──│ Push to DockerHub│◀──│ Build Docker Image   │
└─────────────────────┘   └──────────────────┘   └──────────────────────┘
```

| Stage | Description |
|-------|-------------|
| **1. Checkout** | Clones the `main` branch from GitHub |
| **2. Fetch Secrets from Vault** | Retrieves database and Docker Hub credentials from Vault |
| **3. Install Dependencies** | Runs `pip install -r app/requirements.txt` |
| **4. Run Tests** | Executes `pytest` with verbose output |
| **5. Build Docker Image** | Builds the container image tagged with the Jenkins build number |
| **6. Push to Docker Hub** | Authenticates and pushes the image to Docker Hub |
| **7. Deploy with Ansible** | Runs the Ansible playbook to deploy the new image |

### 6.3 Environment Variables

| Variable | Source | Purpose |
|----------|--------|---------|
| `DOCKERHUB_CREDENTIALS` | Jenkins credentials store | Docker Hub username and password |
| `IMAGE_NAME` | Hardcoded | `fraud-detection-api` |
| `IMAGE_TAG` | `${BUILD_NUMBER}` | Unique tag per build |
| `VAULT_ADDR` | Hardcoded | Vault server address |

---

## 7. Configuration Management (Ansible)

### 7.1 Playbook Structure

The Ansible playbook (`site.yml`) applies three roles sequentially on all target hosts:

```yaml
roles:
  - app          # Deploy the fraud-api container
  - monitoring   # Deploy ELK stack
  - k8s          # Apply Kubernetes manifests
```

### 7.2 Role: `app`

Handles deploying the fraud detection API container:
1. **Pulls** the latest Docker image from Docker Hub
2. **Stops** any existing `fraud-api` container
3. **Starts** a new container with `restart_policy: always` on port 8000

### 7.3 Role: `monitoring`

Deploys the ELK monitoring stack:
1. **Elasticsearch** — single-node mode, port 9200
2. **Logstash** — with pipeline config from `/opt/elk/logstash.conf`, port 5044
3. **Kibana** — connected to Elasticsearch, port 5601

### 7.4 Role: `k8s`

Applies Kubernetes manifests:
1. **Deployment** — `deployment.yaml`
2. **Service** — `service.yaml`
3. **HPA** — `hpa.yaml`

---

## 8. Container Orchestration (Kubernetes)

### 8.1 Deployment

- **Replicas:** 2 (minimum)
- **Strategy:** RollingUpdate with `maxSurge: 1` and `maxUnavailable: 0` (zero-downtime deployments)
- **Health Probes:**
  - Readiness probe: `GET /health` (initial delay: 10s, period: 5s)
  - Liveness probe: `GET /health` (initial delay: 15s, period: 10s)
- **Resource Limits:**
  - Requests: 100m CPU, 128Mi memory
  - Limits: 500m CPU, 512Mi memory

### 8.2 Service

- **Type:** LoadBalancer
- **Port mapping:** External port 80 → Container port 8000
- Provides a stable external IP/DNS for accessing the API

### 8.3 Horizontal Pod Autoscaler (HPA)

- **Min replicas:** 2
- **Max replicas:** 10
- **Scaling metric:** Average CPU utilization at 60%
- Automatically scales pods up/down based on traffic load

---

## 9. Monitoring & Logging (ELK Stack)

### 9.1 Logging Pipeline

```
FastAPI App → JSON log file → Logstash → Elasticsearch → Kibana
```

### 9.2 How It Works

1. **Application Logging:** Every prediction request is logged as structured JSON containing timestamp, amount, category, fraud score, and fraud status
2. **Log Collection:** Logstash reads the JSON log file from a shared Docker volume
3. **Log Parsing:** Logstash parses the JSON, extracts the `@timestamp` field, and adds a `service: fraud-api` tag
4. **Log Storage:** Parsed logs are indexed in Elasticsearch with daily indices (`fraud-logs-YYYY.MM.dd`)
5. **Visualization:** Kibana provides search, filtering, and dashboards for real-time fraud monitoring

### 9.3 Logstash Configuration

```
Input:   File input from /app/logs/app.log (JSON codec)
Filter:  ISO8601 date parsing + service field tagging
Output:  Elasticsearch (fraud-logs-* index) + stdout (debug)
```

### 9.4 Sample Log Entry

```json
{
    "timestamp": "2026-05-12T18:05:00.123456",
    "amount": 4500.0,
    "merchant_category": "online_retail",
    "hour_of_day": 2,
    "distance_from_home_km": 1200.0,
    "is_foreign_transaction": 1,
    "fraud_score": -0.5,
    "is_fraud": true
}
```

---

## 10. Secrets Management (HashiCorp Vault)

### 10.1 Configuration

- Vault runs in **dev mode** via Docker Compose with root token `root`
- Listens on port 8200

### 10.2 Access Policy

The `vault-policy.hcl` defines restricted access:

| Path | Capabilities | Purpose |
|------|-------------|---------|
| `secret/fraud-app/*` | read, list | General app secrets |
| `secret/fraud-app/db` | read | Database credentials |
| `secret/fraud-app/dockerhub` | read | Docker Hub credentials |

### 10.3 Integration with Jenkins

The Jenkins pipeline fetches secrets from Vault at runtime during the "Fetch Secrets from Vault" stage, ensuring credentials are never stored in code or configuration files.

---

## 11. Testing

### 11.1 Test Framework

- **Framework:** pytest with FastAPI TestClient
- **Mocking:** `unittest.mock` to mock the ML model (no real model required for testing)

### 11.2 Test Coverage

| Test Class | Test Case | What It Validates |
|-----------|-----------|-------------------|
| `TestHealthEndpoint` | `test_health_returns_ok` | `/health` returns 200 with `{"status": "ok"}` |
| `TestRootEndpoint` | `test_root_returns_message` | `/` returns 200 with API running message |
| `TestPredictEndpoint` | `test_predict_returns_200` | `/predict` returns 200 for valid input |
| | `test_predict_response_fields` | Response contains `is_fraud`, `fraud_score`, `merchant_category`, `amount` |
| | `test_predict_fraud_detection` | Model prediction `-1` maps to `is_fraud: true` |
| | `test_predict_normal_transaction` | Model prediction `1` maps to `is_fraud: false` |
| | `test_predict_unknown_category_defaults` | Unknown categories default to code `5` (other) |
| | `test_predict_model_receives_correct_features` | Feature array shape is `(1, 5)` |
| | `test_predict_invalid_payload_returns_422` | Invalid data types return 422 |
| | `test_predict_empty_payload_returns_422` | Empty JSON body returns 422 |

### 11.3 Running Tests

```bash
cd app
python -m pytest test_main.py -v
```

---

## 12. Architecture Diagram

```
                    ┌─────────────────────────────────────────────────────┐
                    │                    DEVELOPER                        │
                    │              git push to GitHub                     │
                    └──────────────────────┬──────────────────────────────┘
                                           │
                                           ▼
                    ┌─────────────────────────────────────────────────────┐
                    │               JENKINS CI/CD PIPELINE                │
                    │                                                     │
                    │  Checkout → Vault Secrets → Install → Test →        │
                    │  Docker Build → Docker Push → Ansible Deploy        │
                    └──────────┬──────────────────────────┬───────────────┘
                               │                          │
                   ┌───────────▼───────────┐   ┌─────────▼──────────┐
                   │     DOCKER HUB        │   │   HASHICORP VAULT  │
                   │  (Image Registry)     │   │  (Secrets Store)   │
                   └───────────┬───────────┘   └────────────────────┘
                               │
                   ┌───────────▼───────────────────────────────────────┐
                   │              ANSIBLE DEPLOYMENT                    │
                   │  Role: app → Role: monitoring → Role: k8s         │
                   └───────────┬───────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────────┐
           │                   │                       │
           ▼                   ▼                       ▼
   ┌───────────────┐  ┌───────────────────┐  ┌────────────────────┐
   │  FRAUD API    │  │    ELK STACK      │  │   KUBERNETES       │
   │  (Docker)     │  │                   │  │                    │
   │  Port 8000    │  │ Elasticsearch:9200│  │ 2-10 pods (HPA)   │
   │               │──│ Logstash:5044     │  │ RollingUpdate      │
   │  /predict     │  │ Kibana:5601       │  │ Health Probes      │
   │  /health      │  │                   │  │ LoadBalancer       │
   └───────────────┘  └───────────────────┘  └────────────────────┘
           │                   ▲
           │   JSON Logs       │
           └───────────────────┘
```

---

## 13. How to Run

### 13.1 Prerequisites
- Python 3.11+
- Docker Desktop
- Kaggle dataset: `fraudTrain.csv` placed in `app/`

### 13.2 Local Development

```bash
# Train the model
cd app && python train.py

# Run tests
python -m pytest test_main.py -v

# Start the API
uvicorn main:app --host 0.0.0.0 --port 8000

# Run the simulator
python simulate.py
```

### 13.3 Docker Compose (Full Stack)

```bash
cd docker
docker-compose up -d
```

This starts all 5 services. Access:
- API: http://localhost:8000
- Kibana: http://localhost:5601
- Elasticsearch: http://localhost:9200
- Vault: http://localhost:8200

### 13.4 Kubernetes Deployment

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

---

## 14. Key DevOps Practices Demonstrated

| Practice | Implementation |
|----------|---------------|
| **Continuous Integration** | Jenkins auto-triggers on git push, runs tests |
| **Continuous Deployment** | Jenkins builds, pushes, and deploys via Ansible |
| **Infrastructure as Code** | Ansible roles, Kubernetes YAML manifests |
| **Containerization** | Docker image for consistent deployment |
| **Orchestration** | Kubernetes with rolling updates and auto-scaling |
| **Centralized Logging** | ELK Stack with structured JSON logs |
| **Secrets Management** | HashiCorp Vault with least-privilege policies |
| **Health Monitoring** | Kubernetes readiness and liveness probes |
| **Auto-Scaling** | HPA scales 2–10 pods based on CPU utilization |
| **Zero-Downtime Deployment** | RollingUpdate with maxUnavailable: 0 |
| **Automated Testing** | pytest with mocked ML model for fast, reliable tests |

---

## 15. Dataset

- **Source:** Kaggle — Sparkov Data Generation (Fraud Detection)
- **URL:** https://www.kaggle.com/datasets/kartik2112/fraud-detection
- **File:** `fraudTrain.csv` (~500 MB, 1.3M+ transactions)
- **Features used:** Transaction amount, merchant category, time of day, geographical distance, fraud label

---

## 16. Conclusion

This project demonstrates a complete end-to-end MLOps pipeline for fraud detection, covering the full lifecycle from model training to production deployment with monitoring. The integration of Jenkins CI/CD, Docker containerization, Kubernetes orchestration, ELK logging, and Vault secrets management showcases industry-standard DevOps practices for deploying machine learning applications at scale.

---

*Project by Atul S Patil*
*SPE Final Project — Fraud Detection DevOps Pipeline*
