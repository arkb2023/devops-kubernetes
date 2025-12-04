## Exercise 3.4.1. Kustomize `log-output` and `ping-pong` apps

Deploy `log-output` and `ping-pong` applications (with PostgreSQL backend) using a single kubectl command via Kustomize and deploy it to Google Kubernetes Engine.

**Key Changes from Base**
- Consolidated `apps/ping-pong-log-output/`: Single folder contains YAMLs for PostgreSQL + ping-pong + log-output apps  
- `environments/gke/kustomization.yaml`: Top-level entry point references gateway + app bundle  
- Namespace injection: `namespace: exercises` in app kustomization auto-applies to all resources  

<pre>
  devops-kubernetes/
  ├── apps/ping-pong-log-output/          # Consolidated app manifests
  │   ├── kustomization.yaml              # Links all app resources
  │   ├── postgresql-statefulset.yaml     # PostgreSQL StatefulSet 
  │   ├── postgresql-service.yaml         # PostgreSQL Service 
  │   ├── postgresql-configmap.yaml       # PostgreSQL ConfigMap
  │   ├── ping-pong-deployment.yaml       # ping-pong Deployment 
  │   ├── ping-pong-service.yaml          # ping-pong Service
  │   ├── ping-pong-route.yaml            # ping-pong HTTPRoute
  │   ├── log-output-deployment.yaml      # log-output Deployment
  │   ├── log-output-service.yaml         # log-output Service 
  │   ├── log-output-configmap.yaml       # log-output ConfigMap
  │   └── log-output-route.yaml           # log-output HTTPRoute 
  └── environments/gke/                   # GKE-specific overlays
      ├── kustomization.yaml              # TOP LEVEL entry point
      ├── namespace.yaml                  # Namespace
      └── gateway.yaml                    # Gateway API
</pre>

- Base versions used:  
  - [Ping pong and Log output v3.4](https://github.com/arkb2023/devops-kubernetes/tree/3.4/ping-pong)  
  
***


### 1. **Directory and File Structure**
<pre>
├── apps
│   ├── ping-pong-log-output
│   │   ├── kustomization.yaml
│   │   ├── log-output-configmap.yaml
│   │   ├── log-output-deployment.yaml
│   │   ├── log-output-ingress.yaml
│   │   ├── log-output-route.yaml
│   │   ├── log-output-service.yaml
│   │   ├── ping-pong-deployment.yaml
│   │   ├── ping-pong-ingress.yaml
│   │   ├── ping-pong-route.yaml
│   │   ├── ping-pong-service.yaml
│   │   ├── postgresql-configmap.yaml
│   │   ├── postgresql-init-script-configmap.yaml
│   │   ├── postgresql-service.yaml
│   │   └── postgresql-statefulset.yaml
├── environments
│   └── gke
│       ├── gateway.yaml
│       ├── kustomization.yaml
│       └── namespace.yaml
├── log_output
│   ├── README.md
│   ├── generator
│   │   ├── Dockerfile
│   │   └── generator.py
│   └── reader
│       ├── Dockerfile
│       └── reader.py
├── ping-pong
│   ├── Dockerfile
│   ├── README.md
│   └── pingpong.py
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
    --num-nodes=3 \
    --machine-type=e2-medium \
    --gateway-api=standard \
    --disk-size=50 \
    --enable-ip-alias
  ```
- **Fetch and configure Kubernetes cluster access credentials locally, enabling kubectl to authenticate and manage the specified GKE cluster**  
  ```bash
  gcloud container clusters get-credentials dwk-cluster --zone=asia-south1-a
  ```
- **Namespace creation:**
  ```bash
  kubectl create namespace exercises
  ```

### 3. **Deploy to Kubernetes**

- **Deploy PostgreSQL**:  
  ```bash
  kubectl apply -k environments/gke
  ```
  ```text
  namespace/exercises configured
  configmap/log-output-config created
  configmap/postgres-db-config created
  service/log-output-svc created
  service/ping-pong-svc created
  service/postgresql-db-svc created
  deployment.apps/log-output-dep created
  deployment.apps/ping-pong-dep created
  statefulset.apps/postgresql-db created
  gateway.gateway.networking.k8s.io/log-ping-app-gateway created
  httproute.gateway.networking.k8s.io/log-output-route created
  httproute.gateway.networking.k8s.io/ping-pong-route created
  ```

- **Verify all 3 pods Running**
  ```bash
  kubectl get pods -n exercises -w  
  ```
  *Output*
  ```text
  NAME                              READY   STATUS    RESTARTS   AGE
  log-output-dep-86b9b9dd59-hsgsk   1/1     Running   0          13m
  ping-pong-dep-88554df46-bfxgn     1/1     Running   0          2m45s
  postgresql-db-0                   1/1     Running   0          13m
  postgresql-db-1                   1/1     Running   0          13m
  ```


- **Wait for GKE Gateway controller to fully set up the external load balancer**
  ```bash
  kubectl get gateway log-ping-app-gateway -n exercises -w
  ```
  **Output**
  ```text
  NAME                   CLASS                            ADDRESS       PROGRAMMED   AGE
  log-ping-app-gateway   gke-l7-global-external-managed   136.110.197.45   True         14m
  ```
  > Wait for `ADDRESS` to populate and `PROGRAMMED` to switch to True

- **Verify overall health of the configured entities**
  ```bash
  kubectl get all -n exercises
  ```
  ```text
  NAME                                  READY   STATUS    RESTARTS   AGE
  pod/log-output-dep-86b9b9dd59-hsgsk   1/1     Running   0          14m
  pod/ping-pong-dep-88554df46-bfxgn     1/1     Running   0          3m40s
  pod/postgresql-db-0                   1/1     Running   0          14m
  pod/postgresql-db-1                   1/1     Running   0          14m

  NAME                        TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
  service/log-output-svc      ClusterIP   34.118.232.97    <none>        80/TCP     14m
  service/ping-pong-svc       ClusterIP   34.118.239.158   <none>        3456/TCP   14m
  service/postgresql-db-svc   ClusterIP   None             <none>        5432/TCP   14m

  NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
  deployment.apps/log-output-dep   1/1     1            1           14m
  deployment.apps/ping-pong-dep    1/1     1            1           14m

  NAME                                        DESIRED   CURRENT   READY   AGE
  replicaset.apps/log-output-dep-86b9b9dd59   1         1         1       14m
  replicaset.apps/ping-pong-dep-864bbcd696    0         0         0       14m
  replicaset.apps/ping-pong-dep-88554df46     1         1         1       3m41s

  NAME                             READY   AGE
  statefulset.apps/postgresql-db   2/2     14m
  ```

### 4. Validate

  Use the Gateway Address (http://136.110.197.45/) to access the applications: 
- **Test Log Output App response on `/` HTTP endpoint:**  

  - Application returns the expected response  
    ![caption](../log_output/images/01-log-output-response.png)  

- **Test Ping Pong App response on `/pings` HTTP endpoint:**  

  - Application returns the expected response    
    ![caption](../log_output/images/02-ping-pong-pings-response.png)
      

- **Test Ping Pong App response on `/pingpong` HTTP endpoint:**  

  - Application returns the expected response    
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
  statefulset postgresql-db

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