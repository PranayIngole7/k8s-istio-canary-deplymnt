# Kubernetes Canary Deployment with Istio

A DevOps project demonstrating **canary releases, weighted traffic routing, and rollback** using Kubernetes, Minikube, and Istio.

---

## Objectives

- Deploy stable v1.0 and canary v2.0 versions of a Flask application.
- Control traffic distribution using Istio.
- Test multiple traffic-splitting strategies.
- Verify application health and roll back traffic safely.

---

## Architecture

```mermaid
flowchart TD
    U[HTTP Client] --> G[Istio Ingress Gateway]
    G --> V[VirtualService]
    V --> D[DestinationRule]
    D -->|80% default traffic| S[Stable Flask v1.0]
    D -->|20% default traffic| C[Canary Flask v2.0]

    P[Prometheus] -.->|Scrapes Envoy metrics| G
    P -.->|Scrapes sidecar metrics| S
    P -.->|Scrapes sidecar metrics| C
```

The application runs locally in Minikube. Istio routes incoming requests
between the stable and canary versions according to the VirtualService
configuration.

Prometheus collects Istio and Envoy metrics by scraping configured metrics
endpoints. The dotted arrows represent monitoring, not application request
traffic.

The default routing configuration sends 80% of requests to stable v1.0
and 20% to canary v2.0. The rollback configuration sends 100% to stable v1.0.

---

## Technology Stack and Tools

| Category           | Technologies                  |
| ------------------ | ----------------------------- |
| Application        | Python, Flask                 |
| Containers         | Docker                        |
| Orchestration      | Kubernetes, Minikube, kubectl |
| Traffic management | Istio, Envoy                  |
| Monitoring         | Prometheus, Grafana           |
| Scripting          | Bash, Python                  |

---

## Key Features

- Separate Kubernetes Deployments for stable and canary versions.
- Istio Gateway, VirtualService, and DestinationRule configuration.
- 80/20, 50/50, 100%-canary, and 100%-stable routing scenarios.
- Automated HTTP traffic testing and response counts.
- Health probes and configuration validation.
- Rollback to stable v1.0 without removing the canary Deployment.

---

## Verified Results

Six ingress traffic scenarios were tested with 100 requests each on
21 October 2026.

| Scenario       | Stable | Canary | Errors |
| -------------- | -----: | -----: | -----: |
| 80/20 baseline |     76 |     24 |      0 |
| Stable only    |    100 |      0 |      0 |
| 80/20 retest   |     81 |     19 |      0 |
| 50/50          |     49 |     51 |      0 |
| Canary only    |      0 |    100 |      0 |
| Final rollback |    100 |      0 |      0 |

All six tests completed without unknown responses or request errors.
Finite samples may differ from configured weights.

**Final routing state:** 100% stable v1.0 and 0% canary v2.0.
Prometheus telemetry collection was verified. Grafana is installed, but
dashboard visualization was not validated.

---

## Screenshots

**Stable application — v1.0**

![Stable application v1.0](screenshots/stable-application-v1.png)

**Canary application — v2.0**

![Canary application v2.0](screenshots/canary-application-v2.png)

![Istio Gateway validation](screenshots/istio-gateway-validation.png)

![Rollback validation](screenshots/canary-rollback-validation.png)

---

## How to Run

### Prerequisites

- Install Docker, Minikube, `kubectl`, and `istioctl`.
- Start Minikube and install Istio 1.31.2.

**Prerequisite:** Ensure the `istio-ingressgateway` Service exists in the `istio-system` namespace. This repository does not install Istio or configure the ingress Gateway.

### 1. Build and load the images

Run from the repository root:

```bash
docker build -t canary-demo:v1.0 ./app/stable
docker build -t canary-demo:v2.0 ./app/canary

minikube image load canary-demo:v1.0
minikube image load canary-demo:v2.0
```

### 2. Configure the namespace

```bash
kubectl create namespace canary-demo \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl label namespace canary-demo istio-injection=enabled --overwrite
```

### 3. Deploy the application and Istio resources

```bash
kubectl apply -f k8s/stable-deployment.yaml
kubectl apply -f k8s/canary-deployment.yaml
kubectl apply -f k8s/stable-service.yaml
kubectl apply -f k8s/istio/canary-service.yaml
kubectl apply -f k8s/istio/destination-rule.yaml
kubectl apply -f k8s/istio/gateway.yaml
kubectl apply -f k8s/istio/virtual-service.yaml

kubectl rollout status deployment/stable-app -n canary-demo
kubectl rollout status deployment/canary-app -n canary-demo
istioctl analyze -n canary-demo
```

### 4. Test traffic

In a separate terminal, start the ingress port-forward:

```bash
kubectl port-forward -n istio-system \
  svc/istio-ingressgateway 18080:80
```

Check application health:

```bash
curl -i -H 'Host: canary-demo.local' \
  http://127.0.0.1:18080/healthz
```

Run 100 distribution-test requests:

```bash
./scripts/test-distribution.sh 100
```

### Rollback

Route all traffic to stable v1.0:

```bash
kubectl apply -f k8s/istio/virtual-service-rollback.yaml
```

Restore the 80/20 demonstration configuration when needed:

```bash
kubectl apply -f k8s/istio/virtual-service.yaml
```

---

## Canary Performance Evaluation

`scripts/evaluate-canary.py` evaluates Prometheus request counts, HTTP 5xx
errors, and p95 latency to recommend whether the canary meets configured
performance thresholds. It also checks the current Istio routing weights.

- Minimum canary requests: 50
- Maximum 5xx error rate: 1%
- Maximum p95 latency: 500 ms
- Maximum canary-to-stable p95 latency ratio: 1.5x
- Evaluation window: 5 minutes

Ensure Prometheus is accessible at `http://127.0.0.1:19090`. If needed,
start a port-forward in a separate terminal:

```bash
kubectl port-forward -n monitoring service/prometheus-server 19090:80
```

Run the evaluator:

```bash
python3 scripts/evaluate-canary.py
```
Run its tests:
```bash
python3 -m unittest discover -s tests -p "test_evaluate_canary.py" -v
```

The evaluator requires accessible Prometheus telemetry and active canary
traffic. It provides recommendations only; it does not automatically promote
or roll back the canary. Thresholds are demonstration defaults, not production
SLOs.

---

## Repository Structure

- `app/` — stable and canary Flask applications.
- `k8s/` — Kubernetes Deployments, Services, and Istio manifests.
- `scripts/` — traffic generation, distribution tests, and Prometheus-based canary evaluation.
- `tests/` — automated tests for evaluator decision logic.
- `screenshots/` — application and validation screenshots.
- `reports/` — local traffic-test reports.

---

## Scope

This project demonstrates progressive delivery and metrics-based canary
evaluation in a local Kubernetes environment. Cloud deployment and
production-grade high availability are outside its current scope.

---