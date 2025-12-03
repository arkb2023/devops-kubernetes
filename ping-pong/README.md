## Exercise 3.3. To the Gateway

Replace `Ingress` with Kubernetes `Gateway API` using `HTTPRoute` for path-based routing to `ping-pong` and `log-output` applications.

**Key Changes from Base**
  - [`ping-pong/manifests/gateway.yaml`](./manifests/gateway.yaml) - Single HTTP listener port 80 with `log-ping-app-gateway` LoadBalancer
  - [`ping-pong/manifests/ping-pong-route.yaml`](./manifests/ping-pong-route.yaml) - HTTPRoute `/pingpong` and `/pings` to `ping-pong-svc:3456`
  - [`log_output/manifests/log-output-route.yaml`](../log_output/manifests/log-output-route.yaml) - HTTPRoute `/` to `log-output-svc:80`

- Base versions used:  
  - [Ping pong and Log output v3.2](https://github.com/arkb2023/devops-kubernetes/tree/3.2/ping-pong)  
  
***

### 1. **Directory and File Structure**
<pre>
log_output
├── README.md
├── manifests
│   ├── log-output-route.yaml
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── ingress.yaml
│   ├── service.yaml
│   └── reader
│       ├── Dockerfile
│       └── reader.py
ping-pong/
├── Dockerfile
├── README.md
├── manifests
│   ├── deployment.yaml
│   ├── gateway.yaml
│   ├── ingress.yaml
│   ├── ping-pong-route.yaml
│   └── service.yaml
└── pingpong.py
postgresql/
├── postgresql-configmap.yaml
├── postgresql-service.yaml
└── postgresql-statefulset.yaml
</pre>

***


### 2. Prerequisites (GCP/GKE)

- **Google Cloud CLI** (`gcloud`) updated to 548.0.0
- **kubectl** (Kubernetes CLI) with `gke-gcloud-auth-plugin`
- **GCP Project**: `dwk-gke-480015` configured
- **Cluster Creation**:
  ```bash
  gcloud container clusters create dwk-cluster \
    --zone=asia-south1-a \
    --cluster-version=1.32 \
    --disk-size=32 \
    --num-nodes=3 \
    --machine-type=e2-micro
  ```
- **Enable Gateway API on the cluster**  
  ```bash
  gcloud container clusters update dwk-cluster \
    --zone=asia-south1-a \
    --gateway-api=standard
  ```
- **Fetch and configure Kubernetes cluster access credentials locally, enabling kubectl to authenticate and manage the specified GKE cluster**  
  ```bash
  gcloud container clusters get-credentials dwk-cluster --zone=asia-south1-a
  ```
- **Utility Variables**:
  ```bash
  export NAMESPACE=exercises
  ```
- **Namespace creation:**
  ```bash
  kubectl create namespace ${NAMESPACE}
  ```

### 3. **Deploy to Kubernetes**

- **Deploy PostgreSQL**:  
  ```bash
  kubectl apply -n exercises \
      -f ./postgresql/postgresql-service.yaml \
      -f ./postgresql/postgresql-configmap.yaml \
      -f ./postgresql/postgresql-statefulset.yaml
  ```
- **Wait for the Pods to be in Running state**
  ```bash
  kubectl get pods -n ${NAMESPACE} -l app=postgresql-db
  kubectl describe pods -n ${NAMESPACE}  -l app=postgresql-db
  ```

- **PVC Should show Bound status**
  ```bash
  kubectl get pvc -n ${NAMESPACE}
  ```

- **Initialize database table**
  ```bash
    kubectl exec -n $NAMESPACE postgresql-db-0 -- psql -U testdbuser -d testdb -c "
    CREATE TABLE IF NOT EXISTS pingpong_counter (
        id SERIAL PRIMARY KEY,
        value INTEGER NOT NULL DEFAULT 0
    );
    INSERT INTO pingpong_counter (id, value) VALUES (1, 0) ON CONFLICT (id) DO NOTHING;
    SELECT 'Table ready!' as status;
    "
  ```

- **Deploy `ping-pong` application**
  ```bash
  kubectl apply -n exercises \
    -f ./ping-pong/manifests/deployment.yaml \
    -f ./ping-pong/manifests/service.yaml
  ```

- **Wait for the Pods to be in Running state**
  ```bash
  kubectl get pods -n ${NAMESPACE} -l app=ping-pong
  ```

- **Deploy `log-output` application**
  ```bash
  kubectl apply -n exercises \
      -f ./log_output/manifests/deployment.yaml \
      -f ./log_output/manifests/configmap.yaml \
      -f ./log_output/manifests/service.yaml
  ```

- **Wait for the Pods to be in Running state**
  ```bash
  kubectl get pods -n ${NAMESPACE} -l app=log-output
  ```
  
- **Deploy Gateway**
  ```bash
  kubectl apply -n exercises -f ping-pong/manifests/gateway.yaml
  ```
  *Output*
  ```text
  gateway.gateway.networking.k8s.io/log-ping-app-gateway created
  ```
- **Verify gateway status**
  ```bash
  kubectl -n ${NAMESPACE} describe gateway log-ping-app-gateway
  ```
  *Output*
  ```text
  Name:         log-ping-app-gateway
  Namespace:    exercises
  Labels:       <none>
  Annotations:  networking.gke.io/last-reconcile-time: 2025-12-03T16:43:04Z
  API Version:  gateway.networking.k8s.io/v1
  Kind:         Gateway
  Metadata:
    Creation Timestamp:  2025-12-03T16:42:59Z
    Finalizers:
      gateway.finalizer.networking.gke.io
    Generation:        1
    Resource Version:  1764780184308495017
    UID:               c361f45e-2271-40cb-8a84-1a474bc676ff
  Spec:
    Gateway Class Name:  gke-l7-global-external-managed
    Listeners:
      Allowed Routes:
        Namespaces:
          From:  Same
      Name:      pingpong
      Port:      80
      Protocol:  HTTP
  Status:
    Conditions:
      Last Transition Time:  2025-12-03T16:43:04Z
      Message:               The OSS Gateway API has deprecated this condition, do not depend on it.
      Observed Generation:   1
      Reason:                Scheduled
      Status:                True
      Type:                  Scheduled
      Last Transition Time:  2025-12-03T16:43:04Z
      Message:
      Observed Generation:   1
      Reason:                Accepted
      Status:                True
      Type:                  Accepted
    Listeners:
      Attached Routes:  0
      Conditions:
        Last Transition Time:  2025-12-03T16:43:04Z
        Message:
        Observed Generation:   1
        Reason:                ResolvedRefs
        Status:                True
        Type:                  ResolvedRefs
        Last Transition Time:  2025-12-03T16:43:04Z
        Message:
        Observed Generation:   1
        Reason:                Accepted
        Status:                True
        Type:                  Accepted
      Name:                    pingpong
      Supported Kinds:
        Group:  gateway.networking.k8s.io
        Kind:   HTTPRoute
  Events:
    Type    Reason  Age   From                   Message
    ----    ------  ----  ----                   -------
    Normal  ADD     58s   sc-gateway-controller  exercises/log-ping-app-gateway
    Normal  UPDATE  58s   sc-gateway-controller  exercises/log-ping-app-gateway
  ```
- **Deploy HTTP-Routes for `ping-pong` application**
  ```bash
  kubectl apply -n exercises -f ping-pong/manifests/ping-pong-route.yaml  
  ```
  *Output*
  ```text
  httproute.gateway.networking.k8s.io/ping-pong-route created
  ```
- **Verify route configuration**
  ```bash
  kubectl  -n exercises describe httproute ping-pong-route
  ```
  *Output*
  ```text
  Name:         ping-pong-route
  Namespace:    exercises
  Labels:       <none>
  Annotations:  <none>
  API Version:  gateway.networking.k8s.io/v1
  Kind:         HTTPRoute
  Metadata:
    Creation Timestamp:  2025-12-03T16:46:04Z
    Generation:          1
    Resource Version:    1764780364460479020
    UID:                 20c99bac-b68a-4d27-adbc-8bcd93fed3ec
  Spec:
    Parent Refs:
      Group:  gateway.networking.k8s.io
      Kind:   Gateway
      Name:   log-ping-app-gateway
    Rules:
      Backend Refs:
        Group:
        Kind:    Service
        Name:    ping-pong-svc
        Port:    3456
        Weight:  1
      Matches:
        Path:
          Type:   PathPrefix
          Value:  /pingpong
        Path:
          Type:   PathPrefix
          Value:  /pings
  Events:
    Type    Reason  Age   From                   Message
    ----    ------  ----  ----                   -------
    Normal  ADD     69s   sc-gateway-controller  exercises/ping-pong-route
  ```
- **Deploy HTTP-Routes for `log-output` application**
  ```bash
  kubectl apply -n exercises -f log_output/manifests/log-output-route.yaml  
  ```
  *Output*
  ```text
  httproute.gateway.networking.k8s.io/log-output-route created
  ```
- **Verify route configuration**
  ```bash
  kubectl -n exercises describe httproute log-output-route
  ```
  *Output*
  ```text
  Name:         log-output-route
  Namespace:    exercises
  Labels:       <none>
  Annotations:  <none>
  API Version:  gateway.networking.k8s.io/v1
  Kind:         HTTPRoute
  Metadata:
    Creation Timestamp:  2025-12-03T16:46:18Z
    Generation:          1
    Resource Version:    1764780378928639013
    UID:                 ab25f5a6-001b-45f5-8d83-e1ebe073fc9d
  Spec:
    Parent Refs:
      Group:  gateway.networking.k8s.io
      Kind:   Gateway
      Name:   log-ping-app-gateway
    Rules:
      Backend Refs:
        Group:
        Kind:    Service
        Name:    log-output-svc
        Port:    8080
        Weight:  1
      Matches:
        Path:
          Type:   PathPrefix
          Value:  /
  Events:
    Type    Reason  Age   From                   Message
    ----    ------  ----  ----                   -------
    Normal  ADD     29s   sc-gateway-controller  exercises/log-output-route
  ```
- **Verify all 3 pods Running**
  ```bash
  kubectl get pods -n exercises -w  
  ```
  *Output*
  ```text
  NAME                              READY   STATUS    RESTARTS   AGE
  log-output-dep-65d4dd9b55-ldbgt   1/1     Running   0          46s
  ping-pong-dep-7f68b8df89-sm4p2    1/1     Running   0          20m
  postgresql-db-0                   1/1     Running   0          23m
  postgresql-db-1                   1/1     Running   0          23m
  ```
- **Wait for GKE Gateway controller to fully set up the external load balancer**
  ```bash
  kubectl get gateway log-ping-app-gateway -n exercises -w
  ```
  **Output**
  ```text
  NAME                   CLASS                            ADDRESS       PROGRAMMED   AGE
  log-ping-app-gateway   gke-l7-global-external-managed   34.8.36.183   True         14m
  ```
  > Wait for `ADDRESS` to populate and `PROGRAMMED` to switch to True
- **Verify overall health of the configured entities**
  ```bash
  kubectl get all -n exercises
  ```
  ```text
  NAME                                  READY   STATUS    RESTARTS   AGE
  pod/log-output-dep-65d4dd9b55-ldbgt   1/1     Running   0          13m
  pod/ping-pong-dep-7f68b8df89-sm4p2    1/1     Running   0          33m
  pod/postgresql-db-0                   1/1     Running   0          36m
  pod/postgresql-db-1                   1/1     Running   0          35m

  NAME                        TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
  service/log-output-svc      ClusterIP   34.118.238.160   <none>        80/TCP     32m
  service/ping-pong-svc       ClusterIP   34.118.233.57    <none>        3456/TCP   33m
  service/postgresql-db-svc   ClusterIP   None             <none>        5432/TCP   36m

  NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
  deployment.apps/log-output-dep   1/1     1            1           32m
  deployment.apps/ping-pong-dep    1/1     1            1           33m

  NAME                                        DESIRED   CURRENT   READY   AGE
  replicaset.apps/log-output-dep-65d4dd9b55   1         1         1       13m
  replicaset.apps/log-output-dep-86b9b9dd59   0         0         0       32m
  replicaset.apps/ping-pong-dep-7f68b8df89    1         1         1       33m

  NAME                             READY   AGE
  statefulset.apps/postgresql-db   2/2     36m
  ```

### 4. Validate

  Use the Gateway Address (http://34.8.36.183/) to access the applications: 
- **Test Log Output App response on `/` HTTP endpoint:**  

  - Application returns the expected response  
    ![caption](../log_output/images/01-log-output-response.png)  

- **Test Ping Pong App response on `/pings` HTTP endpoint:**  

  - Application returns `0` *(consistent with previous log-output app response as expected)*  
    ![caption](../log_output/images/02-ping-pong-pings-response.png)
      

- **Test Ping Pong App response on `/pingpong` HTTP endpoint:**  

  - Application returns `N+1` value as expected  
    ![caption](../log_output/images/03-ping-pong-pingpong-response.png)  

### 6. **Cleanup**

**Delete the provisioned resources**
```bash
kubectl delete -n exercises \
    httproute ping-pong-route log-output-route
kubectl delete -n exercises \
    gateway log-ping-app-gateway
kubectl delete -n exercises \
  deployment ping-pong-dep log-output-dep
  
kubectl delete -n exercises \
  statefulset postgresql-db \

kubectl delete -n exercises \
  service ping-pong-svc log-output-svc postgresql-db-svc
  
kubectl delete -n exercises configmap log-output-config
  
# Wait for termination
kubectl get all -n exercises

kubectl delete pvc -n exercises --all  
kubectl delete namespace exercises 
```
<!--GKE Cluster Cleanup (Full Reset)
# Get credentials off cluster
kubectl config delete-context $(kubectl config current-context)
-->
**Delete GKE cluster**
```bash
gcloud container clusters delete dwk-cluster \
  --zone=asia-south1-a \
  --quiet
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