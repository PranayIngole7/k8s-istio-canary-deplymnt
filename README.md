# Kubernetes Canary Deployment with Istio on Minikube

## Objective

Demonstrate progressive application delivery by deploying stable and
canary application versions to Kubernetes and gradually shifting traffic
between them using Istio.

## Technology Stack

- Python and Flask
- Docker
- Kubernetes
- Minikube
- Istio
- kubectl

## Project Status

### Completed

- Created and tested the Flask stable application.
- Built the Docker image `canary-demo:v1.0`.
- Verified the application health endpoint.
- Deployed the stable application to Minikube.
- Configured Kubernetes readiness and liveness probes.
- Created a ClusterIP Service for internal application access.
- Verified the application through Kubernetes port forwarding.

### Remaining Work

- Deploy the canary application version.
- Configure Istio traffic management.
- Implement and verify stable/canary traffic splitting.
- Observe traffic distribution and application behavior.
- Test rollback and promotion procedures.
- Document the final deployment and testing results.

## Kubernetes Resources

| Resource   | Name           | Purpose                                 |
| ---------- | -------------- | --------------------------------------- |
| Deployment | stable-app     | Runs the stable application             |
| Service    | stable-service | Provides internal access to stable pods |

## Deploy the Stable Version

Build the Docker image:

```bash
docker build -t canary-demo:v1.0 ./app
```
Ensure the image is available in Minikube:
```bash
minikube image load canary-demo:v1.0
```

Validate and apply the Kubernetes manifests:
```bash
kubectl apply --dry-run=client -f k8s/
kubectl apply -f k8s/
kubectl rollout status deployment/stable-app --timeout=120s
```

Inspect the deployed resources:
```bash
kubectl get deployments,pods,services
```

## Test the Application

Start port forwarding:
```bash
kubectl port-forward --address 127.0.0.1 service/stable-service 18081:80
```

In another terminal, test the health endpoint:
```bash
curl -i http://127.0.0.1:18081/healthz
```

Test the application:
```bash
curl -i http://127.0.0.1:18081/
```
The health endpoint should return HTTP 200. The main page should identify
version 1.0 as the Stable deployment.

## Planned Deliverables
- Kubernetes Deployment and Service manifests.
- Stable and canary application versions.
- Istio routing configuration.
- Traffic distribution and verification results.
- Rollback and promotion procedure.
- Final project report of no more than two pages, covering the introduction, abstract, tools, implementation steps, and conclusion.
