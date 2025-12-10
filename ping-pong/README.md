## Exercise 4.1. Readines probe
**Instructions:**  
Create a `ReadinessProbe` for the `Ping-pong` application. It should be ready when it has a connection to the database.

And another `ReadinessProbe` for `Log output` application. It should be ready when it can receive data from the `Ping-pong` application.

Test that it works by applying everything but the database `statefulset`. The output of `kubectl get po` should look like this before the database is available:

```text
NAME                             READY   STATUS    RESTARTS   AGE
logoutput-dep-7f49547cf4-ttj4f   1/2     Running   0          21s
pingpong-dep-9b698d6fb-jdgq9     0/1     Running   0          21s
```

Adding the database should automatically move the `READY` states to `2/2` and `1/1` for `Log output` and `Ping-pong` respectively.

---
**Key Changes from Base**

- [`ping-pong-deployment.yaml`](../apps/ping-pong-log-output/ping-pong-deployment.yaml):  
  - Added a `readinessProbe` using `httpGet` on the `/healthz` endpoint to mark the Ping-pong pod Ready only when the PostgreSQL database is reachable.

- [`log-output-deployment.yaml`](../apps/ping-pong-log-output/log-output-deployment.yaml):  
  - Added a `readinessProbe` using `httpGet` on the `/healthz` endpoint for the main `log-reader` container so it is Ready as soon as the HTTP server is up.  
  - Added a `ping-pong-fetcher` sidecar container with an `exec`-based `readinessProbe` that runs `curl` against the `Ping-pong` app `/pings` endpoint, making the Pod fully Ready only when Ping-pong is reachable.

- Log output application [`reader.py`](../log_output/reader/reader.py):  
  - Implemented a `/healthz` route that returns a simple status for the main container’s readiness check.

- Ping-pong application [`pingpong.py`](./pingpong.py):  
  - Implemented a `/healthz` route that executes a lightweight `SELECT 1` against PostgreSQL to drive the DB-backed readiness probe.

- Base application:  
  - [Ping pong and Log output v3.4](https://github.com/arkb2023/devops-kubernetes/tree/3.4/ping-pong)


### 1. **Directory and File Structure**
<pre>
environments/                                   # Multi-env overlays (local/GKE)
├── exercises-gke                               # GKE environment specific overlays
│   ├── gateway.yaml                            # Gateway API
│   ├── kustomization.yaml                      # Top level kustomization entry point 
│   ├── log-output-route.yaml                   # log-output HTTPRoute
│   ├── namespace.yaml                          # Namespace
│   └── ping-pong-route.yaml                    # ping-pong HTTPRoute
├── exercises-local                             # Local k3d environment specific overlays
│   ├── kustomization.yaml                      # Top level kustomization entry point
│   ├── log-output-ingress.yaml                 # log-output ingress
│   ├── namespace.yaml                          # Namespace
│   └── ping-pong-ingress.yaml                  # Ping-pong ingress
  
apps/                                           # Shared base resources
├── ping-pong-log-output                        # Consolidated app manifests + kustomization
│   ├── kustomization.yaml                      # Base manifests for ping-pong + log-output
│   ├── log-output-configmap.yaml               # log-output ConfigMap
│   ├── log-output-deployment.yaml              # log-output Deployment
│   ├── log-output-service.yaml                 # log-output Service 
│   ├── ping-pong-deployment.yaml               # ping-pong Deployment 
│   ├── ping-pong-service.yaml                  # ping-pong Service
│   ├── postgresql-configmap.yaml               # PostgreSQL ConfigMap
│   ├── postgresql-service.yaml                 # PostgreSQL Service
│   └── postgresql-statefulset.yaml             # PostgreSQL StatefulSet 

# Ping Pong application
ping-pong/
├── Dockerfile
├── README.md
└── pingpong.py

# Log output application
log_output/
├── generator
│   ├── Dockerfile
│   └── generator.py
└── reader
    ├── Dockerfile
    └── reader.py
</pre>

  
***

### 2. Setup  
- Docker  
- k3d (K3s in Docker)  
- kubectl (Kubernetes CLI)
- Create Cluster 
  ```bash
  k3d cluster create dwk-local --agents 2 --port 8081:80@loadbalancer
  ```

### 3. **Deploy Without Database (Phase 1)**  

- **Temporarily disable PostgreSQL**:
  - Comment out [`postgresql-statefulset.yaml`](../apps/ping-pong-log-output/postgresql-statefulset.yaml) in [`kustomization.yaml`](../apps/ping-pong-log-output/kustomization.yaml)  
- **Deploy base resources**:
  ```bash
  kustomize build environments/exercises-local/ | kubectl apply -f -
  ```
  Output:
  ```text
  namespace/exercises created
  configmap/log-output-config created
  configmap/postgres-db-config created
  service/log-output-svc created
  service/ping-pong-svc created
  service/postgresql-db-svc created
  deployment.apps/log-output-dep created
  deployment.apps/ping-pong-dep created
  ingress.networking.k8s.io/dwk-log-output-ingress created
  ingress.networking.k8s.io/dwk-ping-pong-ingress created
  ```

### 4. **Verify Pods Status (DB Not Available)**
  **Expected READY states**: `log-output-dep: 1/2`, `ping-pong-dep: 0/1`  

  - **Live Monitor**:  
    ```bash
    kubectl -n exercises get pods  -w  
    ```
    *Output*
    ```text
    NAME                              READY   STATUS    RESTARTS   AGE
    log-output-dep-5cbc778798-6nbk9   0/2     Running   0          4s
    ping-pong-dep-6967f55cd8-4dqzb    0/1     Running   0          4s
    log-output-dep-5cbc778798-6nbk9   1/2     Running   0          35s
    ```
    Explanation:  
    - At 4sec,  
      - The `log-output` pod show `0/2 Running` as no readiness probe triggered yet since the `initialDelaySeconds` is set to `30sec`  
      - The `ping-pong` pod show `0/1 Running` as no readiness probe triggered yet since the `initialDelaySeconds` is set to `30sec`
    - At 35s,
      - The `log-output` pod show `1/2 Running` as readiness probe was successful
      - No update in `ping-pong` pod implying it still in `0/1 Running` state. The readiness probe triggered but as the database is unavailable it responds with `503` indicating not Ready.

  - **Application Logs Confirm**:
    - **Log-output** (`log-reader` container passes): 
      ```bash
      kubectl -n exercises logs log-output-dep-5cbc778798-6nbk9 -f
      ```
      Output:  
      ```text
      Defaulted container "log-reader" out of: log-reader, ping-pong-fetcher
      INFO:     Started server process [7]
      INFO:     Waiting for application startup.
      2025-12-09 17:41:55,007 [log-output] DEBUG Lifespan startup: initializing resources
      INFO:     Application startup complete.
      INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)
      INFO:     10.42.0.1:50168 - "GET /healthz HTTP/1.1" 200 OK
      INFO:     10.42.0.1:39426 - "GET /healthz HTTP/1.1" 200 OK
      INFO:     10.42.0.1:39440 - "GET /healthz HTTP/1.1" 200 OK
      INFO:     10.42.0.1:46864 - "GET /healthz HTTP/1.1" 200 OK
      INFO:     10.42.0.1:46868 - "GET /healthz HTTP/1.1" 200 OK
      INFO:     10.42.0.1:59920 - "GET /healthz HTTP/1.1" 200 OK
      ```
    - **Ping-pong** (DB probe fails):

      ```bash
      kubectl -n exercises logs ping-pong-dep-6967f55cd8-4dqzb |grep GET |tail -10
      ```
      Output:  
      ```text
      INFO:     10.42.2.1:41394 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      INFO:     10.42.2.1:41404 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      INFO:     10.42.2.1:35242 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      INFO:     10.42.2.1:35252 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      INFO:     10.42.2.1:40886 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      INFO:     10.42.2.1:40890 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      INFO:     10.42.2.1:40892 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      INFO:     10.42.2.1:38704 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      INFO:     10.42.2.1:38708 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      INFO:     10.42.2.1:36752 - "GET /healthz HTTP/1.1" 503 Service Unavailable
      ```
  - **Final State**:     
    ```bash
    kubectl -n exercises get pods
    ```
    Output:  
    ```text
    NAME                              READY   STATUS    RESTARTS   AGE
    log-output-dep-5cbc778798-6nbk9   1/2     Running   0          14m
    ping-pong-dep-6967f55cd8-4dqzb    0/1     Running   0          14m
    ```
    > At 14mins, both applications continue to remain in same state as expected
  

### 5. **Automatic Recovery (DB Available)**
  **Expected**: Pods flip from `0/1 + 1/2` to `1/1 + 2/2` automatically   

  - **Deploy PostgreSQL**:
    ```bash
    kubectl -n exercises apply -f apps/ping-pong-log-output/postgresql-statefulset.yaml
    ```
    Output:  
    ```text
    statefulset.apps/postgresql-db created
    ```
  - Live Monitor the status as the `postgresql-db` pods initialize  
    ```bash
    kubectl -n exercises get pods  -w
    ```
    Output:  
    ```text
    NAME                              READY   STATUS    RESTARTS   AGE
    log-output-dep-5cbc778798-6nbk9   1/2     Running   0          17m
    ping-pong-dep-6967f55cd8-4dqzb    0/1     Running   0          17m
    postgresql-db-0                   0/1     Pending   0          4s
    postgresql-db-0                   0/1     Pending   0          4s
    postgresql-db-0                   0/1     ContainerCreating   0          4s
    postgresql-db-0                   0/1     Running             0          10s
    postgresql-db-0                   1/1     Running             0          15s
    postgresql-db-1                   0/1     Pending             0          0s
    postgresql-db-1                   0/1     Pending             0          3s
    postgresql-db-1                   0/1     ContainerCreating   0          3s
    ping-pong-dep-6967f55cd8-4dqzb    1/1     Running             0          18m
    postgresql-db-1                   0/1     Running             0          7s
    postgresql-db-1                   1/1     Running             0          12s
    ```
  - **Final State**:     
    ```bash
    kubectl -n exercises get pods
    ```
    Output:  
    ```text
    NAME                              READY   STATUS    RESTARTS   AGE
    log-output-dep-5cbc778798-6nbk9   2/2     Running   0          18m
    ping-pong-dep-6967f55cd8-4dqzb    1/1     Running   0          18m
    postgresql-db-0                   1/1     Running   0          41s
    postgresql-db-1                   1/1     Running   0          26s
    ```
    > As expected,  
    >   `log-output` status show `2/2`   
    >   `ping-pong` status show `1/1`  

  - **Ping-pong Logs** (503 → 200 transition):  
    ```bash
    kubectl -n exercises logs ping-pong-dep-6967f55cd8-4dqzb -f
    ```
    Output:  
    ```text
    INFO:     10.42.2.1:39178 - "GET /healthz HTTP/1.1" 503 Service Unavailable
    2025-12-09 18:00:02,129 [ping-pong] ERROR healthz DB error: gaierror(-2, 'Name or service not known')
    INFO:     10.42.2.1:39188 - "GET /healthz HTTP/1.1" 503 Service Unavailable
    2025-12-09 18:00:06,382 [ping-pong] DEBUG healthz: db connection responsive
    INFO:     10.42.2.1:41242 - "GET /healthz HTTP/1.1" 200 OK
    2025-12-09 18:00:11,321 [ping-pong] DEBUG healthz: db connection responsive
    INFO:     10.42.2.1:41258 - "GET /healthz HTTP/1.1" 200 OK
    2025-12-09 18:00:16,322 [ping-pong] DEBUG healthz: db connection responsive
    INFO:     10.42.2.1:53232 - "GET /healthz HTTP/1.1" 200 OK
    2025-12-09 18:00:21,321 [ping-pong] DEBUG healthz: db connection responsive
    INFO:     10.42.2.1:53248 - "GET /healthz HTTP/1.1" 200 OK
    2025-12-09 18:00:26,322 [ping-pong] DEBUG healthz: db connection responsive
    INFO:     10.42.2.1:34926 - "GET /healthz HTTP/1.1" 200 OK
    ```
### 6. **Cleanup**

**Delete resources**
```bash
kubectl delete namespace exercises 
```
**Delete Cluster**
```bash
k3d cluster delete dwk-local
```

<!--
# Verify deletion
gcloud container clusters list --project=dwk-gke-480015

# Verification Commands
# Check namespace empty
kubectl get all -n exercises  # No resources

# Check no lingering PVCs
kubectl get pvc -n exercises  # No resources

# Check cluster clean
kubectl get nodes  # Context error = clean

---
check logs
kubectl -n ${NAMESPACE} logs postgresql-db-1 -c postgresql-db
kubectl -n ${NAMESPACE} logs postgresql-db-0 -c postgresql-db 
# live logs
kubectl -n ${NAMESPACE} logs -f postgresql-db-1
-->

