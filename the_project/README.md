## Exercise 4.2. The project, step 21
**Instructions:**  
Create the required probes and endpoint for The Project to ensure that it's working and connected to a database.  

Test that the probe indeed works with a version without database access, for example by supplying a wrong database URL or credentials.  

---

**Key Changes from Base**

- [`todo-backend-deployment.yaml`](../apps/the-project/todo-backend-deployment.yaml):  
  - Added a `readinessProbe` using `httpGet` on the `/healthz` endpoint to mark the Todo-backend pod Ready only when the PostgreSQL database is reachable.

- [`todo-app-deployment.yaml`](../apps/the-project/todo-app-deployment.yaml):  
  - Added a `readinessProbe` using `httpGet` on the `/healthz` endpoint for the main `todo-app` container so it is Ready as soon as the HTTP server is up.  
  - Added a `todo-backend-fetcher` sidecar container with an `exec`-based `readinessProbe` that runs `curl` against the `todo-backend` app `/todos/healthz` endpoint, making the Pod fully Ready only when `todo-backend` is reachable.

- Todo application (frontend) [`todo_app/app/routes/frontend.py`](./todo_app/app/routes/frontend.py):  
  - Implemented a `/healthz` route that returns a simple status for the main container’s readiness check.  

- Todo-backend application [`todo_backend/app/routes/todos.py`](./todo_backend/app/routes/todos.py):  
  - Implemented a `/healthz` route that executes a lightweight `SELECT 1` against PostgreSQL to drive the DB-backed readiness probe.

- Base application:  
  - [Todo App and Todo Backend v3.12](https://github.com/arkb2023/devops-kubernetes/tree/3.12/the_project)


### 1. **Directory and File Structure**
<pre>

environments/                                   # Multi-env overlays (k3dlocal/GKE)
├── project-gke                                 # GKE environment specific overlays
│   ├── gateway.yaml                            # Gateway API (GKE)
│   ├── kustomization.yaml                      # Top level kustomization entry point 
│   ├── namespace.yaml                          # Namespace
│   ├── persistentvolumeclaim.yaml              # Persistent Volume Claim
│   ├── podmonitoring-todo-backend.yaml         # Pod monitoring
│   ├── postgresql-backup-cronjob.yaml          # PostgreSQL Backup Cronbjob
│   ├── todo-app-route.yaml                     # Todo-App HTTPRoute (GKE)
│   └── todo-backend-route.yaml                 # Todo-backend App HTTPRoute (GKE)
└── project-local                               # k3d Local environment specific overlays
    ├── kustomization.yaml                      # Top level kustomization entry point 
    ├── namespace.yaml                          # Namespace
    ├── persistentvolume.yaml                   # Persistent Volume
    ├── persistentvolumeclaim.yaml              # Persistent Volume Claim
    └── todo-ingress.yaml                       # Traefik ingress

apps/                                           # Shared base resources
└── the-project                                 # Consolidated app manifests + kustomization
    ├── cron_wiki_todo.yaml                     # Wiki Generator CronJob
    ├── kustomization.yaml                      # Base manifests for Todo App, Todo backend, Postgress and Wiki Generator
    ├── postgresql-configmap.yaml               # PostgreSQL ConfigMap
    ├── postgresql-dbsecret.yaml                # PostgreSQL Secret
    ├── postgresql-service.yaml                 # PostgreSQL Service
    ├── postgresql-statefulset.yaml             # PostgreSQL StatefulSet
    ├── todo-app-configmap.yaml                 # Todo Application ConfigMap
    ├── todo-app-deployment.yaml                # Todo Application Deployment
    ├── todo-app-service.yaml                   # Todo Application Service
    ├── todo-backend-configmap.yaml             # Todo Backend Application ConfigMap
    ├── todo-backend-deployment.yaml            # Todo Backend Application Deployment
    └── todo-backend-service.yaml               # Todo Backend Application Service

the_project/                                    # Project root
├── todo_app                                    # Frontend application
│   ├── Dockerfile                              # Dockerfile for image
│   ├── app                                     # Application code
│   │   ├── __init__.py
│   │   ├── cache.py
│   │   ├── main.py
│   │   ├── routes
│   │   │   ├── __init__.py
│   │   │   └── frontend.py
│   │   ├── static
│   │   │   └── scripts.js
│   │   └── templates
│   │       └── index.html
│   └── requirements.txt
└── todo_backend                                # Backend application
    ├── Dockerfile                              # Dockerfile for image
    ├── app                                     # Application code
    │   ├── __init__.py
    │   ├── main.py
    │   ├── models.py
    │   ├── routes
    │   │   ├── __init__.py
    │   │   └── todos.py
    │   └── storage.py
    └── requirements.txt

# Deployment flow:
# kustomize build environments/project-local | kubectl apply -f -
# kustomize build environments/project-gke | kubectl apply -f -

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

### 3. **Deploy with wrong database URL**  

**Test Case: Invalid PostgreSQL hostname triggers readiness probe failure**

  - **Temporarily supply wrong PostgreSQL URL**:
    - Edit ConfigMap [`todo-backend-configmap.yaml`](../apps/the-project/todo-backend-configmap.yaml):  
    ```
    DB_HOST: postgresql-db-svc-invalid  # CHANGED (invalid)
    # was: postgresql-db-svc (valid)
    ```

  - **Deploy resources**:
    ```bash
    kustomize build  environments/project-local | kubectl apply -f -
    ```
    Output:
    ```text
    namespace/project created
    serviceaccount/postgres-backup-sa created
    configmap/postgres-db-config created
    configmap/todo-app-config created
    configmap/todo-backend-config created
    secret/postgres-db-secret created
    service/postgresql-db-svc created
    service/todo-app-svc created
    service/todo-backend-svc created
    persistentvolume/local-pv created
    persistentvolumeclaim/local-pv-claim created
    deployment.apps/todo-app-dep created
    deployment.apps/todo-backend-dep created
    statefulset.apps/postgresql-db created
    cronjob.batch/postgres-backup created
    cronjob.batch/wiki-todo-generator created
    ingress.networking.k8s.io/todo-ingress created
    ```

  - **Config map shows wrong PostgreSQL URL**:
    ```bash
    kubectl -n project describe configmaps todo-backend-config
    ```
    Output:
    ```text
    Name:         todo-backend-config
    Namespace:    project
    Labels:       app=todo-backend
    Annotations:  <none>

    Data
    ====
    DB_HOST:
    ----
    postgresql-db-svc-invalid     # INVALID HOSTNAME

    DB_PORT:
    ----
    5432
    ```

### 4. **Verify Pods Status (DB Not Available)**  
  **Expected READY states**: `todo-app-dep: 1/2`, `todo-backend-dep: 0/1`  
  - **Live Monitor**:  
    ```bash
    kubectl -n project get pod -w  
    ```
    *Output*
    ```text
    NAME                                READY   STATUS              RESTARTS   AGE
    postgresql-db-0                     0/1     ContainerCreating   0          6s
    todo-app-dep-6c6cfc68b9-59bxp       0/2     Running             0          6s
    todo-backend-dep-7b9d466c54-k8x79   0/1     Running             0          6s
    postgresql-db-0                     1/1     Running             0          7s
    todo-app-dep-6c6cfc68b9-59bxp       1/2     Running             0          10s

    ```
    **Explanation**:  
    - `todo-app-dep`: `1/2 Ready`
      - Frontend healthy (`/healthz` works!)
      - Backend-fetcher sidecar contiainer probe `curl` failed - NotReady  
    - `todo-backend-dep`: `0/1 Ready`
      - Backend NotReady (`/todos/healthz` returns 503 due to DB unreachable)

  - **Todo-App logs** (frontend healthy):
    ```bash
    kubectl -n project logs todo-app-dep-6c6cfc68b9-59bxp -f
    ```
    Output:  
    ```text
    Defaulted container "todo-app-container" out of: todo-app-container, todo-backend-fetcher
    ENV: 2025-12-11 10:09:37,412 - app.cache - INFO - cache,py module loaded: LOG_LEVEL=DEBUG, LOG_FORMAT=ENV: %(asctime)s - %(name)s - %(levelname)s - %(message)s
    ENV: 2025-12-11 10:09:37,412 - todo-app - INFO - frontend.py module loaded: LOG_LEVEL=DEBUG, LOG_FORMAT=ENV: %(asctime)s - %(name)s - %(levelname)s - %(message)s, backend_api=/todos/
    INFO:     Started server process [7]
    INFO:     Waiting for application startup.
    ENV: 2025-12-11 10:09:37,413 - app.cache - INFO - Loading metadata from /usr/src/app/files/cache/cache_metadata.json
    ENV: 2025-12-11 10:09:37,413 - app.cache - INFO - Loaded metadata: {'grace_period_used': False, 'access_count': 0, 'last_access_time': None, 'download_timestamp': 1765447111.3773715, 'image_access_count': 0}
    ENV: 2025-12-11 10:09:37,413 - app.cache - INFO - ImageCache initialized with cache_dir: /usr/src/app/files/cache, ttl: 600s
    ENV: 2025-12-11 10:09:37,413 - todo-app - INFO - Lifespan startup: Cache initialized with dir /usr/src/app/files/cache
    ENV: 2025-12-11 10:09:37,413 - app.cache - INFO - Cache age: 666.0365164279938s, TTL: 600s, Expired: True
    ENV: 2025-12-11 10:09:37,413 - todo-app - INFO - Lifespan startup: Cache is expired on startup, fetching new image
    ENV: 2025-12-11 10:09:37,413 - app.cache - INFO - Fetching new image from external source
    ENV: 2025-12-11 10:09:37,413 - app.cache - INFO - cache,py img_url: https://picsum.photos/500
    ENV: 2025-12-11 10:09:43,728 - app.cache - INFO - Image fetched and cached successfully at 1765447783.7287328
    ENV: 2025-12-11 10:09:43,729 - todo-app - INFO - Lifespan startup: Image fetched and cached successfully on startup
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)
    ENV: 2025-12-11 10:09:46,386 - todo-app - DEBUG - todo app health response OK!
    INFO:     10.42.0.1:39470 - "GET /healthz HTTP/1.1" 200 OK
    ENV: 2025-12-11 10:09:51,385 - todo-app - DEBUG - todo app health response OK!
    INFO:     10.42.0.1:39474 - "GET /healthz HTTP/1.1" 200 OK
    ```
    > *Key lines:*  
    > INFO: Uvicorn running on http://0.0.0.0:3000  
    > INFO: 10.42.0.1:39470 - "GET /healthz HTTP/1.1" 200 OK # <-- Frontend probe passes  
 
  - **Todo-backend logs** (DB address resolution failure as expected):

    ```bash
    kubectl -n project logs todo-backend-dep-7b9d466c54-k8x79 -f
    ```
    Output:  
    ```text
    2025-12-11 10:09:37,715 [todo_backend] INFO DB_HOST=postgresql-db-svc-invalid
    2025-12-11 10:09:37,715 [todo_backend] INFO DB_PORT=5432
    2025-12-11 10:09:37,715 [todo_backend] INFO POSTGRES_DB=testdb
    2025-12-11 10:09:37,715 [todo_backend] INFO POSTGRES_USER=testdbuser
    2025-12-11 10:09:37,715 [todo_backend] INFO POSTGRES_PASSWORD=testdbuserpassword
    2025-12-11 10:09:37,715 [todo_backend] INFO storage.py: Final DB URL: postgresql+asyncpg://testdbuser:testdbuserpassword@postgresql-db-svc-invalid:5432/testdb
    2025-12-11 10:09:39,807 [todo_backend] WARNING Database Table Creation: Attempt 1/3 failed: [Errno -5] No address associated with hostname
    2025-12-11 10:09:42,819 [todo_backend] WARNING Database Table Creation: Attempt 2/3 failed: [Errno -5] No address associated with hostname
    2025-12-11 10:09:45,826 [todo_backend] WARNING Database Table Creation: Attempt 3/3 failed: [Errno -5] No address associated with hostname
    2025-12-11 10:09:46,828 [todo_backend] ERROR Database not ready after max retries; continuing without DB
    2025-12-11 10:09:53,406 [todo_backend] ERROR healthz DB error: [Errno -5] No address associated with hostname
    2025-12-11 10:09:53,406 [todo_backend] WARNING todo_http_error
    INFO:     10.42.0.1:51232 - "GET /todos/healthz HTTP/1.1" 503 Service Unavailable
    2025-12-11 10:09:58,194 [todo_backend] ERROR healthz DB error: [Errno -5] No address associated with hostname
    INFO:     10.42.0.1:39834 - "GET /todos/healthz HTTP/1.1" 503 Service Unavailable
    2025-12-11 10:09:58,195 [todo_backend] WARNING todo_http_error
    ```

    > *Key lines:*  
    > Final DB URL: postgresql+asyncpg://testdbuser:testdbuserpassword@postgresql-db-svc-invalid:5432/testdb  # <-- Invalid URL  
    > WARNING Database Table Creation: Attempt 1/3 failed: [Errno -5] No address associated with hostname  
    > ERROR healthz DB error: [Errno -5] No address associated with hostname  
    > INFO: 10.42.0.1:51232 - "GET /todos/healthz HTTP/1.1" 503 Service Unavailable                           # <-- Probe fails  

  - **Final State**:     
    ```bash
    kubectl -n project get pod
    ```
    Output:  
    ```text
    NAME                                READY   STATUS    RESTARTS   AGE
    postgresql-db-0                     1/1     Running   0          2m28s
    todo-app-dep-6c6cfc68b9-59bxp       1/2     Running   0          2m28s
    todo-backend-dep-7b9d466c54-k8x79   0/1     Running   0          2m28s
    ```
    > Pods NotReady:  
    > `todo-app-dep: 1/2` - NotReady due to Backend NotReady  
    > `todo-backend-dep: 0/1` - NotReady due to DB unreachable  

### 5. **Automatic Recovery (DB Available)**
  **Expected**: Pods flip from `0/1 + 1/2` to `1/1 + 2/2` automatically   

  - **Fix the PostgreSQL URL**:
    - Edit ConfigMap [`todo-backend-configmap.yaml`](../apps/the-project/todo-backend-configmap.yaml) and set `DB_HOST: postgresql-db-svc` (valid)

  - **Deploy fixed ConfigMap**:
    ```bash
    kubectl apply -f ../../apps/the-project/todo-backend-configmap.yaml
    ```
    Output:  
    ```text
    configmap/todo-backend-config configured
    ```

  - **Restart the backend deployment**
    ```bash
    kubectl -n project rollout restart deploy todo-backend-dep
    ```
    Output:  
    ```text
    deployment.apps/todo-backend-dep restarted
    ```

  - Live Monitor the status as the `todo-backend-dep` pods initialize  
    ```bash
    kubectl -n project get pod -w
    ```
    Output:  
    ```text
    NAME                                READY   STATUS    RESTARTS   AGE
    postgresql-db-0                     1/1     Running   0          6m12s
    todo-app-dep-6c6cfc68b9-59bxp       1/2     Running   0          6m12s
    todo-backend-dep-7b9d466c54-k8x79   0/1     Running   0          6m12s
    todo-backend-dep-7b4868bc88-xh9qs   0/1     Pending   0          0s
    todo-backend-dep-7b4868bc88-xh9qs   0/1     Pending   0          0s
    todo-backend-dep-7b4868bc88-xh9qs   0/1     ContainerCreating   0          0s
    todo-backend-dep-7b4868bc88-xh9qs   0/1     Running             0          2s
    todo-backend-dep-7b4868bc88-xh9qs   1/1     Running             0          15s
    todo-backend-dep-7b9d466c54-k8x79   0/1     Terminating         0          7m1s
    todo-app-dep-6c6cfc68b9-59bxp       2/2     Running             0          7m2s
    todo-backend-dep-7b9d466c54-k8x79   0/1     Error               0          7m31s
    todo-backend-dep-7b9d466c54-k8x79   0/1     Error               0          7m32s
    todo-backend-dep-7b9d466c54-k8x79   0/1     Error               0          7m32s
    ```

  - **Final State**:     
    ```bash
    kubectl -n project get pod
    ```
    Output:  
    ```text
    NAME                                READY   STATUS    RESTARTS   AGE
    postgresql-db-0                     1/1     Running   0          7m45s
    todo-app-dep-6c6cfc68b9-59bxp       2/2     Running   0          7m45s
    todo-backend-dep-7b4868bc88-xh9qs   1/1     Running   0          59s
    ```
    > As expected, after correcting DB_HOST the backend becomes 1/1 Ready, and the frontend pod transitions from 1/2 to 2/2 Ready once the backend health check starts returning 200.

  - **Todo-backend Logs** (200 OK database response):  
    ```bash
    kubectl -n project logs todo-backend-dep-7b4868bc88-xh9qs -f
    ```
    Output:  
    ```text
    2025-12-11 10:16:24,395 [todo_backend] INFO DB_HOST=postgresql-db-svc
    2025-12-11 10:16:24,396 [todo_backend] INFO DB_PORT=5432
    2025-12-11 10:16:24,396 [todo_backend] INFO POSTGRES_DB=testdb
    2025-12-11 10:16:24,396 [todo_backend] INFO POSTGRES_USER=testdbuser
    2025-12-11 10:16:24,396 [todo_backend] INFO POSTGRES_PASSWORD=testdbuserpassword
    2025-12-11 10:16:24,396 [todo_backend] INFO storage.py: Final DB URL: postgresql+asyncpg://testdbuser:testdbuserpassword@postgresql-db-svc:5432/testdb
    2025-12-11 10:16:24,640 [todo_backend] INFO Database ready!
    2025-12-11 10:16:37,863 [todo_backend] DEBUG healthz: todo backend db connection responsive
    INFO:     10.42.0.1:54702 - "GET /todos/healthz HTTP/1.1" 200 OK
    2025-12-11 10:16:38,633 [todo_backend] DEBUG healthz: todo backend db connection responsive
    INFO:     10.42.0.111:37768 - "GET /todos/healthz HTTP/1.1" 200 OK
    2025-12-11 10:16:42,860 [todo_backend] DEBUG healthz: todo backend db connection responsive
    INFO:     10.42.0.1:50452 - "GET /todos/healthz HTTP/1.1" 200 OK
    2025-12-11 10:16:43,646 [todo_backend] DEBUG healthz: todo backend db connection responsive
    INFO:     10.42.0.111:46264 - "GET /todos/healthz HTTP/1.1" 200 OK
    2025-12-11 10:16:47,860 [todo_backend] DEBUG healthz: todo backend db connection responsive
    INFO:     10.42.0.1:50466 - "GET /todos/healthz HTTP/1.1" 200 OK
    ```
    > PostgreSQL reachability results in successful health probe responses ("GET /todos/healthz HTTP/1.1" 200 OK), confirming that the DB-backed readiness probe now gates pod readiness correctly

### 6. **Cleanup**

**Delete resources**
```bash
kubectl delete namespace project 
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
