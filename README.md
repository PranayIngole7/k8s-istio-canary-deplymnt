# Kubernetes Canary Deployment with Istio on Minikube

## Objective

Demonstrate progressive application delivery by deploying stable and
canary application versions to Kubernetes and gradually shifting traffic
between them using Istio.

The project uses a local Minikube cluster and does not require cloud
infrastructure.

## Technology Stack

- Python and Flask
- Docker
- Kubernetes and kubectl
- Minikube
- Istio

## Project Status

### Completed

- Implemented the stable Flask application (v1.0).
- Implemented the canary Flask application (v2.0) with an updated interface.
- Built the Docker images `canary-demo:v1.0` and `canary-demo:v2.0`.
- Deployed both application versions to Minikube.
- Configured Kubernetes readiness and liveness probes.
- Created a ClusterIP Service for the stable application.
- Installed Istio 1.31.2 using the minimal profile.
- Enabled automatic Istio sidecar injection in the `canary-demo` namespace.
- Verified that both application Pods are running with their Istio sidecars.
- Verified both application health endpoints return HTTP 200.
- Confirmed that both Envoy proxies are connected to the Istio control plane.
- Ran `istioctl analyze` successfully with no validation issues.
- Removed the previous application deployments and Service from the `default`
  namespace after verifying the new deployments.

### Remaining Work

- Configure Istio Gateway and traffic-routing resources.
- Route requests to the stable and canary versions through a shared Service.
- Implement and verify an 80% stable / 20% canary traffic split.
- Observe traffic distribution and application behavior.
- Test rollback to 100% stable traffic.
- Document the final deployment and testing results.

## Application Versions

| Version | Deployment   | Image              | Purpose                    |
| ------- | ------------ | ------------------ | -------------------------- |
| 1.0     | `stable-app` | `canary-demo:v1.0` | Stable application         |
| 2.0     | `canary-app` | `canary-demo:v2.0` | Updated canary application |

Both applications expose `/healthz` on port 8080.

## Kubernetes Resources

The application resources are deployed in the `canary-demo` namespace.

| Resource   | Name             | Purpose                                 |
| ---------- | ---------------- | --------------------------------------- |
| Deployment | `stable-app`     | Runs stable version 1.0                 |
| Deployment | `canary-app`     | Runs canary version 2.0                 |
| Service    | `stable-service` | Provides internal access to stable Pods |

The stable Service currently selects the stable Pods only. Shared-service
routing and version-based traffic splitting will be configured in the
Istio traffic-management phase.

## Build Application Images

Build the stable image:

```bash
docker build -t canary-demo:v1.0 ./app/stable
```

Build the canary image:
```bash
docker build -t canary-demo:v2.0 ./app/canary
```

Ensure both images are available in Minikube:
```bash
minikube image load canary-demo:v1.0
minikube image load canary-demo:v2.0
```

## Deploy the Applications
Create the namespace and enable automatic sidecar injection:
```bash
kubectl create namespace canary-demo
kubectl label namespace canary-demo istio-injection=enabled
```

The namespace and label commands are for initial setup. If the namespace
already exists, verify it instead of creating it again:
```bash
kubectl get namespace canary-demo --show-labels
```
Validate the manifests and apply the application resources:
```bash
kubectl apply --dry-run=client -f k8s/stable-deployment.yaml
kubectl apply --dry-run=client -f k8s/canary-deployment.yaml
kubectl apply --dry-run=client -f k8s/stable-service.yaml

kubectl apply -f k8s/stable-deployment.yaml
kubectl apply -f k8s/canary-deployment.yaml
kubectl apply -f k8s/stable-service.yaml
```

Wait for both deployments:
```bash
kubectl rollout status deployment/stable-app -n canary-demo --timeout=120s
kubectl rollout status deployment/canary-app -n canary-demo --timeout=120s
```

Inspect the resources:
```bash
kubectl get deployments,pods,services -n canary-demo
```

## Install and Verify Istio
The cluster was checked with `istioctl x precheck` before installation.
Istio was installed using its minimal profile.
```bash
~/istio-1.31.2/bin/istioctl install --set profile=minimal
```

If `istioctl` is not on your PATH, use its full installation path.
For example:
```bash
~/istio-1.31.2/bin/istioctl version
~/istio-1.31.2/bin/istioctl proxy-status
~/istio-1.31.2/bin/istioctl analyze -n canary-demo
```

Expected verification includes:
- Client and control plane versions match.
- Both application proxies appear in `proxy-status`.
- Both application Pods report `2/2 Running`.
- `istioctl analyze` reports no validation issues.

## Test Application Health
Port-forward the stable deployment in one terminal:
```bash
kubectl port-forward -n canary-demo deployment/stable-app 18081:8080
```

In another terminal, test its health endpoint and main page:
```bash
curl -i http://127.0.0.1:18081/healthz
curl -i http://127.0.0.1:18081/
```

Port-forward the canary deployment in a separate terminal:
```bash
kubectl port-forward -n canary-demo deployment/canary-app 18082:8080
```

Test the canary health endpoint and main page:
```bash
curl -i http://127.0.0.1:18082/healthz
curl -i http://127.0.0.1:18082/
```

Both health endpoints should return HTTP 200 with the response `OK`.

The stable main page identifies version 1.0 and the Stable deployment;
the canary main page identifies version 2.0 and the Canary deployment.

Stop each port-forward with Ctrl+C when testing is complete.

## Planned Deliverables
- Stable and canary application source code and container images.
- Kubernetes Deployment and Service manifests.
- Istio Gateway and traffic-routing configuration.
- Verification of the 80/20 traffic split.
- Rollback procedure returning traffic to 100% stable.
- Final project report of no more than two pages, covering the introduction,
  abstract, tools, implementation steps, and conclusion.
