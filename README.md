# Fraud Detection DevOps Pipeline

A real-time financial fraud detection system built with MLOps and DevSecOps practices.

## Tech Stack
- **App:** Python + FastAPI + scikit-learn (Isolation Forest)
- **CI/CD:** Jenkins + GitHub Webhooks
- **Containerization:** Docker + Docker Compose
- **Config Management:** Ansible (with Roles)
- **Orchestration:** Kubernetes + HPA
- **Secrets:** HashiCorp Vault
- **Monitoring:** ELK Stack (Elasticsearch, Logstash, Kibana)

## Project Structure
```
fraud-detection-devops/
├── app/               # FastAPI app + ML model
├── jenkins/           # Jenkinsfile
├── docker/            # Docker Compose
├── ansible/           # Playbooks with roles
├── k8s/               # Kubernetes manifests + HPA
├── elk/               # Logstash config
└── vault/             # Vault policy
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

# 4. Run live transaction simulation
cd ../app && python simulate.py

# 5. View Kibana dashboard
open http://localhost:5601
```

## Vault Setup

```bash
# Start vault in dev mode (already in docker-compose)
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=root

# Store secrets
vault kv put secret/fraud-app/db password=yourdbpassword
vault kv put secret/fraud-app/dockerhub password=yourdockerhubpassword
```

## Trigger CI/CD

Push any change to the `main` branch — Jenkins will automatically:
1. Fetch secrets from Vault
2. Run tests
3. Build Docker image
4. Push to Docker Hub
5. Deploy via Ansible to Kubernetes

## Dataset
Download from Kaggle: https://www.kaggle.com/datasets/kartik2112/fraud-detection  
Place `fraudTrain.csv` in the `app/` folder before running `train.py`
