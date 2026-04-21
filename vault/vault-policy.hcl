# Vault policy for fraud detection app

path "secret/fraud-app/*" {
  capabilities = ["read", "list"]
}

path "secret/fraud-app/db" {
  capabilities = ["read"]
}

path "secret/fraud-app/dockerhub" {
  capabilities = ["read"]
}
