## [Exercise 5.7. Deploy to serverless](https://courses.mooc.fi/org/uh-cs/courses/devops-with-kubernetes/chapter-6/beyond-kubernetes)  

**Instructions**  
Make the Ping-pong application serverless.  
Reading [this](https://knative.dev/docs/serving/convert-deployment-to-knative-service/) might be helpful.  
TIP: Your application should listen on port 8080 or better yet have a PORT environment variable to configure this.

---

### 1. Key Changes from Base

**New Ping-pong Serverless manifest added**
- [pingpong-knative-service.yaml](../apps/ping-pong-serverless/pingpong-knative-service.yaml) - Knative Service `knative-ping-pong-svc` enabling serverless autoscaling-to-zero

**PostgreSQL manifests:** *(Unchanged from previous implementation [v5.3](https://github.com/arkb2023/devops-kubernetes/tree/5.3/ping-pong))*
- [postgresql-configmap.yaml](../apps/ping-pong-serverless/postgresql-configmap.yaml)
- [postgresql-init-script.yaml](../apps/ping-pong-serverless/postgresql-init-script.yaml)
- [postgresql-service.yaml](../apps/ping-pong-serverless/)
- [postgresql-statefulset-patch.yaml](../apps/ping-pong-serverless/postgresql-statefulset-patch.yaml)
- [postgresql-statefulset.yaml](../apps/ping-pong-serverless/postgresql-statefulset.yaml)

**Kustomize Integration**
- [`apps/ping-pong-serverless/`](../apps/ping-pong-serverless/) - Base manifests (Ping-pong serverless + PostgreSQL)  
- [kustomization.yaml](../apps/ping-pong-serverless/kustomization.yaml) - Kustomization entry point  
- [namespace.yaml](../apps/ping-pong-serverless/namespace.yaml) - Creates exercises namespace isolation

---

### 2. Directory and File Structure
<pre>
apps/ping-pong-serverless/            # Consolidated app manifests + kustomization
├── kustomization.yaml                # kustomization entry point
├── namespace.yaml                    # Namespace
├── pingpong-knative-service.yaml     # Knative specification 
├── postgresql-configmap.yaml         # PostgreSQL ConfigMap
├── postgresql-init-script.yaml       # PostgreSQL Init script
├── postgresql-service.yaml           # PostgreSQL Service
├── postgresql-statefulset-patch.yaml # PostgreSQL StatefulSet patch
└── postgresql-statefulset.yaml       # PostgreSQL StatefulSet

ping-pong/                            # Ping Pong application folder
├── Dockerfile                        # Dockerfile for pingpong application
├── README.md                         # Readme
└── pingpong.py                       # Ping Pong application code
</pre>

  
***

### 3. Knative-specific cluster Setup
- Cluster Kubernetes with `v1.32.0-k3s1`
  ```bash
  k3d cluster create dwk-local \
    --image rancher/k3s:v1.32.0-k3s1 \
    --port '8082:30080@agent:0' \
    --port '8081:80@loadbalancer' \
    --agents 2 \
    --k3s-arg "--disable=traefik@server:0"
  ```

- Install Knative Serving CRDs
  ```bash
  kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.20.1/serving-crds.yaml
  ```
- Install the core components of Knative Serving
  ```bash
  kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.20.1/serving-core.yaml
  ```

- Install the Knative Kourier controller
  ```bash
  kubectl apply -f https://github.com/knative-extensions/net-kourier/releases/download/knative-v1.20.0/kourier.yaml
  ```
- Configure Knative Serving to use Kourier by default:
  ```bash
  kubectl patch configmap/config-network \
    --namespace knative-serving \
    --type merge \
    --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
  ```
- Check the External IP address or CNAME by running the command:
  ```bash
  kubectl get svc kourier -n kourier-system
  NAME      TYPE           CLUSTER-IP      EXTERNAL-IP                        PORT(S)                      AGE
  kourier   LoadBalancer   10.43.106.249   172.18.0.2,172.18.0.4,172.18.0.5   80:31129/TCP,443:30848/TCP   20h
  ```
- Configure default-domain that configures Knative Serving to use sslip.io as the default DNS suffix.
  ```bash
  kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.20.1/serving-default-domain.yaml
  ```
- Kourier system gateway pod running
  ```bash
  kubectl get pods -n kourier-system
  Output:
  NAME                                     READY   STATUS    RESTARTS     AGE
  3scale-kourier-gateway-6b9c459c7-7f9tm   1/1     Running   1 (8h ago)   20h
  ```
- Knative component pods healthy
  ```bash
  kubectl get pods -n knative-serving
  # Output
  NAME                                      READY   STATUS      RESTARTS     AGE
  activator-7c67cf64d4-nxjrl                1/1     Running     1 (8h ago)   20h
  autoscaler-5564c5c759-gm5kx               1/1     Running     1 (8h ago)   20h
  controller-7544bfc5db-xtjn8               1/1     Running     1 (8h ago)   20h
  default-domain-98f5z                      0/1     Completed   0            8h
  net-kourier-controller-56fbdbc79f-2mmjm   1/1     Running     1 (8h ago)   20h
  webhook-5c756fc6c5-lqlgg                  1/1     Running     1 (8h ago)   20h
  ###

---

### 4. Deploy Application stack with Kustomize
  ```bash
  kustomize build apps/ping-pong-serverless/ | kubectl apply -f -
  # Output
  namespace/exercises created
  configmap/postgres-db-config created
  configmap/postgres-init-script created
  service.serving.knative.dev/knative-ping-pong-svc created
  service/postgresql-db-svc created
  statefulset.apps/postgresql-db created
  ```
  - Knative Service status
    ```bash
    kubectl -n exercises get ksvc
    NAME                    URL                                                          LATESTCREATED                 LATESTREADY                   READY   REASON
    knative-ping-pong-svc   http://knative-ping-pong-svc.exercises.172.18.0.3.sslip.io   knative-ping-pong-svc-00001   knative-ping-pong-svc-00001   True
    ```
- Application stack up and running
  ```bash
  kubectl -n exercises  get pod -w
  NAME                                                      READY   STATUS    RESTARTS   AGE
  knative-ping-pong-svc-00001-deployment-57bbf8f66c-bkwfn   1/2     Running   0          5s
  postgresql-db-0                                           0/1     Running   0          7s
  postgresql-db-0                                           1/1     Running   0          18s
  knative-ping-pong-svc-00001-deployment-57bbf8f66c-bkwfn   2/2     Running   0          30s
  ```

---

### 5. Test Serverless Ping-pong Application
- Access Knative Service (Triggers Scale UP)
  ```bash

  # /pingpong endpoint
  curl -H "Host: knative-ping-pong-svc.exercises.172.18.0.3.sslip.io" http://localhost:8081/pingpong
  [Knative] pong: 1

  # /pings endpoint
  curl -H "Host: knative-ping-pong-svc.exercises.172.18.0.3.sslip.io" http://localhost:8081/pings
  [Knative] Ping / Pongs: 1
  ```

- Monitor autoscaling Lifecycle
  ```bash
  kubectl -n exercises  get pod -w
  # Output
  NAME              READY   STATUS    RESTARTS   AGE
  postgresql-db-0   1/1     Running   0          10m
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   0/2     Pending   0          0s
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   0/2     Pending   0          0s
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   0/2     ContainerCreating   0          0s
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   1/2     Running             0          1s
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   2/2     Running             0          1s
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   2/2     Terminating         0          62s
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   1/2     Terminating         0          86s
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   0/2     Completed           0          5m45s
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   0/2     Completed           0          5m45s
  knative-ping-pong-svc-00001-deployment-55d4765d6c-pck5g   0/2     Completed           0          5m45s
  ```
  Key Observations:  
  - State Transitions: `Pending > ContainerCreating > Running > Terminating > Completed`  
  - Cold Start: `0/2 Pending > 0/2 ContainerCreating > 1/2 Running > 2/2 Running`  
  - Traffic Window: `2/2 Running` serves requests  
  - Scale-Down: 60s idle → `2/2 Terminating > 0/2 Completed`  

---

### 6. cleanup
```bash
kustomize build apps/ping-pong-serverless/ | kubectl delete -f -
```
---
