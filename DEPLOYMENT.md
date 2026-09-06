# DEPLOYMENT — `mlops-pipeline` live on DigitalOcean (free for 60 days)

Takes you from nothing to a **public, HTTPS** MLOps stack on a DigitalOcean Droplet
running k3s. The $200 / 60-day new-account credit covers a 4 GB Droplet (~$24/mo) for
the **entire job hunt at $0**.

| URL | Serves |
|---|---|
| `https://churn.ajinkya.website` | model API (`/predict`, `/metrics`, `/healthz`) |
| `https://grafana.ajinkya.website` | dashboards (latency, prediction rate) |
| `https://mlflow.ajinkya.website` | experiment tracking + model registry |

**No local Docker.** Images build in GitHub Actions → GHCR; the Droplet pulls them. You
only ever SSH in and run `kubectl`. Replace `ajinkya.website` with your real domain.

---

## 1. Buy a domain (~$1–3/yr)
Register a `.xyz`/`.site` on **Porkbun** or **Namecheap**. That's the only spend if you
stay inside the DO credit.

## 2. DigitalOcean account + credit
1. Sign up at digitalocean.com and add a payment method (needed to unlock the credit;
   you won't be charged while credit remains).
2. Confirm the **$200 / 60-day credit** shows under **Billing**.

## 3. Create the Droplet
**Create → Droplets**:
- Image: **Ubuntu 24.04 LTS**
- Plan: **Basic → Regular**, **4 GB / 2 vCPU** (~$24/mo, free under credit)
- Region: **Bangalore (BLR1)** — closest to you
- Authentication: **SSH key** (add yours; paste your `~/.ssh/id_ed25519.pub`)
- Hostname: `mlops`

Then give it a stable address: **Networking → Reserved IPs → Assign** to the Droplet.
Use that reserved IP everywhere below as `<IP>`.

## 4. Firewall
**Networking → Firewalls → Create**. Inbound rules: allow **SSH 22**, **HTTP 80**,
**HTTPS 443**. Attach it to the `mlops` Droplet. (That's all the ports the stack needs.)

## 5. DNS (in the DigitalOcean dashboard)
Point your domain's nameservers at DigitalOcean (`ns1.digitalocean.com`,
`ns2.digitalocean.com`, `ns3.digitalocean.com`) at your registrar. Then in DO:
**Networking → Domains → add `ajinkya.website`**, and create three **A** records:

| Type | Hostname | Will direct to |
|---|---|---|
| A | churn | `<IP>` |
| A | grafana | `<IP>` |
| A | mlflow | `<IP>` |

Verify: `dig +short churn.ajinkya.website` returns `<IP>`.

## 6. SSH in + install k3s
```bash
ssh root@<IP>
apt update && apt -y upgrade
curl -sfL https://get.k3s.io | sh -
kubectl get nodes                       # Ready?
mkdir -p ~/.kube && cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
export KUBECONFIG=~/.kube/config && echo 'export KUBECONFIG=~/.kube/config' >> ~/.bashrc
kubectl create namespace mlops
```
Install Helm + cert-manager (for automatic HTTPS):
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.3/cert-manager.yaml
kubectl -n cert-manager rollout status deploy/cert-manager-webhook
```

## 7. Build the image (GitHub Actions → GHCR)
1. Push this repo to `github.com/ajinkyatha/mlops-pipeline`.
2. The **MLOps CI** workflow trains, gates, and pushes
   `ghcr.io/ajinkyatha/mlops-pipeline/churn-api:latest`. Wait for a green run in **Actions**.
3. Make it pullable: GitHub → **Packages → churn-api → Package settings → Visibility → Public**.

## 8. Deploy the app + MLflow
```bash
git clone https://github.com/ajinkyatha/mlops-pipeline.git && cd mlops-pipeline
kubectl apply -f k8s/deployment.yaml
kubectl apply -f deploy/mlflow.yaml
kubectl -n mlops rollout status deploy/churn-api
kubectl -n mlops rollout status deploy/mlflow
```

## 9. Prometheus + Grafana
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/prometheus -n mlops \
  --set server.persistentVolume.size=2Gi --set alertmanager.enabled=false
helm install grafana grafana/grafana -n mlops -f deploy/grafana-values.yaml
```

## 10. HTTPS + routing
Edit `deploy/cluster-issuer.yaml` (your email) and `deploy/ingress.yaml` (your domain), then:
```bash
kubectl apply -f deploy/cluster-issuer.yaml
kubectl apply -f deploy/ingress.yaml
kubectl -n mlops get certificate            # wait for READY=True (1–2 min)
```
When the cert is ready, all three HTTPS URLs are live.

## 11. Verify every tool ✅
```bash
# 1. Model API
curl https://churn.ajinkya.website/healthz
curl -X POST https://churn.ajinkya.website/predict -H 'content-type: application/json' \
  -d '{"tenure":3,"monthly_charges":95.0,"support_calls":5,"contract_type":0}'

# 2. Model metrics
curl https://churn.ajinkya.website/metrics | grep model_

# 3. Prometheus scraping (port-forward, then browse localhost:9090 → Status→Targets)
kubectl -n mlops port-forward svc/prometheus-server 9090:80

# 4. Grafana → https://grafana.ajinkya.website (admin / password in deploy/grafana-values.yaml)
#    Import monitoring/grafana/dashboard.json, then generate load:
for i in $(seq 1 200); do curl -s -X POST https://churn.ajinkya.website/predict \
  -H 'content-type: application/json' \
  -d '{"tenure":'$((RANDOM%72))',"monthly_charges":'$((RANDOM%140+15))',"support_calls":'$((RANDOM%6))',"contract_type":'$((RANDOM%3))'}' >/dev/null; done

# 5. MLflow → https://mlflow.ajinkya.website ; log a real run against it:
pip install -r requirements.txt
export MLFLOW_TRACKING_URI=https://mlflow.ajinkya.website
python data/generate_data.py && python src/train.py

# 6. Evidently drift demo
python data/generate_data.py --drift && python src/monitor_drift.py   # writes drift_report.html
```

## 12. Protect the credit / tear down
- The credit lasts 60 days; a 4 GB Droplet burns ~$24/mo, so ~$48 total — well inside $200.
- **Power off** the Droplet in the DO dashboard when idle (you still pay while it exists, so
  to truly stop billing, **Destroy** it and keep only a Snapshot to restore later).
- Full teardown: destroy the Droplet + release the Reserved IP.

## Troubleshooting
- **ImagePullBackOff** → GHCR package isn't Public (step 7).
- **Certificate not READY** → A record not pointing at `<IP>` yet, or DNS not propagated.
- **502** → target pod not Running: `kubectl -n mlops get pods,svc`.
- **Prometheus target DOWN** → check the churn pod's `prometheus.io/*` annotations.
