# Fraud Detection DevOps Pipeline

A real-time financial fraud detection system built with MLOps and DevSecOps practices.

## Tech Stack
- **App:** Python + FastAPI + scikit-learn (Isolation Forest)
- **CI/CD:** Jenkins + GitHub Webhooks (auto-trigger on push)
- **Containerization:** Docker + Docker Compose
- **Config Management:** Ansible (with Roles: app, monitoring, k8s)
- **Orchestration:** Kubernetes + HPA + RollingUpdate (zero-downtime)
- **Secrets:** HashiCorp Vault
- **Monitoring & Logging:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **Testing:** pytest with FastAPI TestClient

## Project Structure
```
fraud-detection-devops/
├── app/                    # FastAPI app + ML model + tests
│   ├── main.py             # API with /predict, /health endpoints
│   ├── train.py            # Isolation Forest model training
│   ├── simulate.py         # Live transaction simulator
│   ├── test_main.py        # Unit tests (pytest)
│   ├── Dockerfile
│   └── requirements.txt
├── jenkins/                # CI/CD pipeline
│   └── Jenkinsfile         # 7-stage pipeline with GitHub webhook trigger
├── docker/                 # Docker Compose stack
│   └── docker-compose.yml  # 5 services: API, ELK, Vault
├── ansible/                # Configuration management
│   ├── site.yml            # Main playbook
│   ├── inventory.ini       # Host inventory
│   └── roles/
│       ├── app/            # Deploy fraud-api container
│       ├── monitoring/     # Deploy ELK stack
│       └── k8s/            # Apply K8s manifests + HPA
├── k8s/                    # Kubernetes manifests
│   ├── deployment.yaml     # RollingUpdate + health probes
│   ├── service.yaml        # LoadBalancer service
│   └── hpa.yaml            # Horizontal Pod Autoscaler (2-10 pods)
├── elk/                    # Logstash pipeline config
│   └── logstash.conf       # JSON log parsing → Elasticsearch
└── vault/                  # Vault access policy
    └── vault-policy.hcl
```

## Quick Start (Local)

```bash
# 1. Train the model (download Sparkov dataset from Kaggle first)
cd app && python train.py

# 2. Start all services
cd ../docker && docker-compose up -d

# 3. Test the API
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"amount": 4500, "merchant_category": "online_retail", "hour_of_day": 2, "distance_from_home_km": 1200, "is_foreign_transaction": 1}'

# 4. Run unit tests
cd ../app && python -m pytest test_main.py -v

# 5. Run live transaction simulation
python simulate.py

# 6. View Kibana dashboard
open http://localhost:5601
```

## Vault Setup

```bash
# Vault starts automatically in dev mode via docker-compose
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=root

# Store secrets
vault kv put secret/fraud-app/db password=yourdbpassword
vault kv put secret/fraud-app/dockerhub password=yourdockerhubpassword
```

## CI/CD Pipeline (Jenkins)

Push any change to the `main` branch — Jenkins auto-triggers via GitHub webhook:

1. **Checkout** — fetch latest code
2. **Fetch Secrets** — retrieve credentials from Vault
3. **Install Dependencies** — pip install requirements
4. **Run Tests** — pytest with verbose output
5. **Build Docker Image** — containerize the app
6. **Push to Docker Hub** — publish image with build number tag
7. **Deploy with Ansible** — roll out to Kubernetes via Ansible playbook

## Kubernetes Features

- **RollingUpdate** strategy with `maxSurge: 1, maxUnavailable: 0` for zero-downtime deployments
- **Readiness & Liveness probes** on `/health` endpoint
- **HPA** scales from 2 to 10 pods at 60% CPU utilization

## Logging Pipeline

Application → JSON logs → Shared volume → Logstash → Elasticsearch → Kibana

The API writes structured JSON log lines for every prediction, which Logstash parses and indexes into daily `fraud-logs-*` indices for Kibana visualization.

## Dataset
Download from Kaggle: https://www.kaggle.com/datasets/kartik2112/fraud-detection
Place `fraudTrain.csv` in the `app/` folder before running `train.py`
