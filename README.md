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
- Verified both application health endpoints return HTTP 200.
- Confirmed that both Envoy proxies are connected to the Istio control plane.
- Created a shared `canary-service` selecting both application versions.
- Configured a DestinationRule with `stable` (v1) and `canary` (v2) subsets.
- Configured a VirtualService with an 80% stable / 20% canary traffic split.
- Ran `istioctl analyze` successfully with no validation issues.
- Tested 100 requests from an application Pod inside the mesh: 78 stable
  responses, 22 canary responses, and zero errors.
- Removed the previous application deployments and Service from the `default`
  namespace after verifying the new deployments.

### Remaining Work

- Configure and validate an Istio Gateway if needed for external access.
- Perform further traffic-distribution and application-behavior checks.
- Test rollback to 100% stable traffic.
- Document the final deployment, testing results, and rollback procedure.
- Complete the final project report of no more than two pages.

## Application Versions

| Version | Deployment   | Image              | Purpose                    |
| ------- | ------------ | ------------------ | -------------------------- |
| 1.0     | `stable-app` | `canary-demo:v1.0` | Stable application         |
| 2.0     | `canary-app` | `canary-demo:v2.0` | Updated canary application |

Both applications expose `/healthz` on port 8080.

## Kubernetes and Istio Resources

The application and traffic-management resources are deployed in the
`canary-demo` namespace.

| Resource        | Name                 | Purpose                                              |
| --------------- | -------------------- | ---------------------------------------------------- |
| Deployment      | `stable-app`         | Runs stable version 1.0                              |
| Deployment      | `canary-app`         | Runs canary version 2.0                              |
| Service         | `stable-service`     | Provides direct internal access to stable Pods       |
| Service         | `canary-service`     | Selects both stable and canary Pods for mesh routing |
| DestinationRule | `canary-destination` | Defines the `stable` (v1) and `canary` (v2) subsets  |
| VirtualService  | `canary-routing`     | Routes 80% of traffic to stable and 20% to canary    |

The weighted routing policy applies to requests routed through the Istio mesh
to `canary-service.canary-demo.svc.cluster.local`. Direct requests or
port-forwards to individual application Deployments are useful for checking
a specific version, but do not by themselves verify the weighted traffic split.

### Traffic-split verification

A test sent 100 HTTP requests from the stable application Pod to the shared
Service through the mesh. The observed results were:

| Result      | Requests | Observed share |
| ----------- | -------: | -------------: |
| Stable v1.0 |       78 |            78% |
| Canary v2.0 |       22 |            22% |
| Errors      |        0 |             0% |

The result is consistent with the configured 80/20 weighted split. Since
routing is probabilistic, a finite sample is not expected to match the
configured percentages exactly.

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

## Traffic Distribution Verification

Istio weighted routing was verified from inside the service mesh using
requests to `canary-service.canary-demo.svc.cluster.local`.

| Test              | Total Requests | Stable v1.0 | Canary v2.0 | Errors |
| ----------------- | -------------: | ----------: | ----------: | -----: |
| Initial test      |            100 |    78 (78%) |    22 (22%) |      0 |
| Verification test |            200 | 159 (79.5%) |  41 (20.5%) |      0 |

Both tests returned no unknown responses or request errors in the
reported results. The observed distribution is consistent with the
configured 80% stable / 20% canary traffic weights.

Additional validation:
- Both application Pods were `2/2 Running`.
- `istioctl analyze -n canary-demo` reported no validation issues.
- Envoy route configuration included `canary-routing.canary-demo`.
- Envoy destination clusters included the stable and canary subsets.

These tests provide evidence that weighted routing is working. The
observed percentages are sample results and are not guaranteed for
every request batch.

## Canary Rollback Verification

A separate rollback manifest is provided at
`k8s/istio/virtual-service-rollback.yaml`.

To direct all traffic to the stable version:

```bash
kubectl apply -f k8s/istio/virtual-service-rollback.yaml
```
The rollback configuration routes 100% of requests to the stable
subset. Both application deployments remain deployed; only the
VirtualService routing policy changes.

| Metric                | Result |
| --------------------- | -----: |
| Requests sent         |    100 |
| Stable v1.0 responses |    100 |
| Canary v2.0 responses |      0 |
| Unknown responses     |      0 |
| Errors                |      0 |

Istio analysis reported no validation issues after applying the
rollback configuration.

To restore the canary demonstration's original 80/20 split:
```bash
kubectl apply -f k8s/istio/virtual-service.yaml
```

The rollback test passed. The original 80/20 routing configuration
was subsequently restored.

## Istio Ingress Gateway Verification

The application is exposed through an Istio HTTP Gateway using the host
`canary-demo.local`. On local Minikube, access it through port-forwarding
to the ingress gateway Service.

### Start local Gateway access

Run this command in a dedicated terminal and leave it running:

```bash
kubectl port-forward -n istio-system svc/istio-ingressgateway 18080:80
```
Test the application health endpoint from another terminal:
```bash
curl -i --max-time 5 -H 'Host: canary-demo.local' \
  http://127.0.0.1:18080/healthz
```
The health check returned HTTP 200 through the Istio ingress Gateway.
Gateway traffic distribution
The VirtualService references both mesh and canary-gateway and
routes traffic through the canary-service DestinationRule subsets.

A 100-request test through the ingress Gateway produced:
| Metric                  | Result |
| ----------------------- | -----: |
| Total requests          |    100 |
| Stable v1.0 responses   |     81 |
| Canary v2.0 responses   |     19 |
| Unknown responses       |      0 |
| Errors                  |      0 |
| Observed Stable traffic |  81.0% |
| Observed Canary traffic |  19.0% |

The observed distribution is consistent with the configured 80/20
weights for this sample. Actual percentages can vary between batches.

Istio validation completed with no configuration issues:
```bash
~/istio-1.31.2/bin/istioctl analyze -n canary-demo
```

## Traffic Distribution Scenario Testing

Traffic distribution scenarios were tested through the Istio ingress Gateway
using `scripts/test-distribution.sh`. Each scenario sent 100 requests to the
application through `http://127.0.0.1:18080/` with the host
`canary-demo.local`.

### Scenario manifests

| Manifest                                    | Stable weight | Canary weight | Purpose                     |
| ------------------------------------------- | ------------: | ------------: | --------------------------- |
| `k8s/istio/virtual-service.yaml`            |           80% |           20% | Canonical baseline          |
| `k8s/istio/virtual-service-50-50.yaml`      |           50% |           50% | Balanced traffic test       |
| `k8s/istio/virtual-service-100-canary.yaml` |            0% |          100% | Route all traffic to canary |
| `k8s/istio/virtual-service-rollback.yaml`   |          100% |            0% | Roll back traffic to stable |

All scenario manifests configure both `mesh` and `canary-gateway`, so the
weights apply to internal mesh routing and the configured ingress Gateway.

### Observed results

| Scenario                  | Stable responses | Canary responses | Unknown | Errors |
| ------------------------- | ---------------: | ---------------: | ------: | -----: |
| Stable rollback (100/0)   |              100 |                0 |       0 |      0 |
| Balanced (50/50)          |               50 |               50 |       0 |      0 |
| Canary-only (0/100)       |                0 |              100 |       0 |      0 |
| Restored baseline (80/20) |               78 |               22 |       0 |      0 |

The final baseline test confirmed that the canonical 80/20 configuration
was restored. Observed percentages can vary between request batches.

### Run a distribution test

Ensure the ingress Gateway port-forward is running in a separate terminal:

```bash
kubectl port-forward -n istio-system svc/istio-ingressgateway 18080:80
```

Then run:
```bash
./scripts/test-distribution.sh 100
```

The script reports stable, canary, unknown, and error counts and writes a
timestamped report under `reports/`. Generated reports are local test
artifacts and are excluded from version control.

To apply a scenario manually, use the appropriate manifest, for example:
```bash
kubectl apply -f k8s/istio/virtual-service-50-50.yaml
```

After scenario testing, restore the baseline:
```bash
kubectl apply -f k8s/istio/virtual-service.yaml
```
