## Exercise 3.4 Rewritten routing

Modifiy the ping-pong app and Gateway API configuration to rewrite the external URL path `/pingpong` to the application root path `/`. This eliminates the need for the app to handle cluster-level path prefixes.

**Key Changes from Base**
  - [`ping-pong/manifests/ping-pong-route.yaml`](./manifests/ping-pong-route.yaml) - Configured URLRewrite filter with `replacePrefixMatch: /` to rewrite `/pingpong` to `/` via Gateway API.
  - [`ping-pong/pingpong.py`](./pingpong.py) - Modified the ping-pong app route handler to respond on the root path `/` instead of `/pingpong`.

- Base versions used:  
  - [Ping pong and Log output v3.3](https://github.com/arkb2023/devops-kubernetes/tree/3.3/ping-pong)  
  
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
  Annotations:  networking.gke.io/addresses: /projects/929711803146/global/addresses/gkegw1-nv9e-exercises-log-ping-app-gateway-v71xu3da78az
                networking.gke.io/backend-services:
                  /projects/929711803146/global/backendServices/gkegw1-nv9e-exercises-gw-serve404-80-t9htdxlbxe5i, /projects/929711803146/global/backendServ...
                networking.gke.io/firewalls: /projects/929711803146/global/firewalls/gkegw1-nv9e-l7-default-global
                networking.gke.io/forwarding-rules: /projects/929711803146/global/forwardingRules/gkegw1-nv9e-exercises-log-ping-app-gateway-tz4nlc0g34o7
                networking.gke.io/health-checks:
                  /projects/929711803146/global/healthChecks/gkegw1-nv9e-exercises-gw-serve404-80-t9htdxlbxe5i, /projects/929711803146/global/healthChecks/g...
                networking.gke.io/last-reconcile-time: 2025-12-04T03:00:56Z
                networking.gke.io/lb-route-extensions:
                networking.gke.io/lb-traffic-extensions:
                networking.gke.io/ssl-certificates:
                networking.gke.io/target-http-proxies:
                  /projects/929711803146/global/targetHttpProxies/gkegw1-nv9e-exercises-log-ping-app-gateway-z33kukono48t
                networking.gke.io/target-https-proxies:
                networking.gke.io/url-maps: /projects/929711803146/global/urlMaps/gkegw1-nv9e-exercises-log-ping-app-gateway-z33kukono48t
                networking.gke.io/wasm-plugin-versions:
                networking.gke.io/wasm-plugins:
  API Version:  gateway.networking.k8s.io/v1
  Kind:         Gateway
  Metadata:
    Creation Timestamp:  2025-12-04T02:59:04Z
    Finalizers:
      gateway.finalizer.networking.gke.io
    Generation:        1
    Resource Version:  1764817256941455017
    UID:               e1513a64-5e6a-42f7-bab0-5d7814a7ece6
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
    Addresses:
      Type:   IPAddress
      Value:  34.8.79.182
    Conditions:
      Last Transition Time:  2025-12-04T02:59:21Z
      Message:               The OSS Gateway API has deprecated this condition, do not depend on it.
      Observed Generation:   1
      Reason:                Scheduled
      Status:                True
      Type:                  Scheduled
      Last Transition Time:  2025-12-04T02:59:21Z
      Message:
      Observed Generation:   1
      Reason:                Accepted
      Status:                True
      Type:                  Accepted
      Last Transition Time:  2025-12-04T03:00:56Z
      Message:
      Observed Generation:   1
      Reason:                Programmed
      Status:                True
      Type:                  Programmed
      Last Transition Time:  2025-12-04T03:00:56Z
      Message:               The OSS Gateway API has altered the "Ready" condition semantics and reserved it for future use.  GKE Gateway will stop emitting it in a future update, use "Programmed" instead.
      Observed Generation:   1
      Reason:                Ready
      Status:                True
      Type:                  Ready
      Last Transition Time:  2025-12-04T03:00:56Z
      Message:
      Observed Generation:   1
      Reason:                Healthy
      Status:                True
      Type:                  networking.gke.io/GatewayHealthy
    Listeners:
      Attached Routes:  0
      Conditions:
        Last Transition Time:  2025-12-04T02:59:21Z
        Message:
        Observed Generation:   1
        Reason:                ResolvedRefs
        Status:                True
        Type:                  ResolvedRefs
        Last Transition Time:  2025-12-04T02:59:21Z
        Message:
        Observed Generation:   1
        Reason:                Accepted
        Status:                True
        Type:                  Accepted
        Last Transition Time:  2025-12-04T03:00:56Z
        Message:
        Observed Generation:   1
        Reason:                Programmed
        Status:                True
        Type:                  Programmed
        Last Transition Time:  2025-12-04T03:00:56Z
        Message:               The OSS Gateway API has altered the "Ready" condition semantics and reserved it for future use.  GKE Gateway will stop emitting it in a future update, use "Programmed" instead.
        Observed Generation:   1
        Reason:                Ready
        Status:                True
        Type:                  Ready
      Name:                    pingpong
      Supported Kinds:
        Group:  gateway.networking.k8s.io
        Kind:   HTTPRoute
  Events:
    Type    Reason  Age                  From                   Message
    ----    ------  ----                 ----                   -------
    Normal  ADD     2m48s                sc-gateway-controller  exercises/log-ping-app-gateway
    Normal  UPDATE  91s (x3 over 2m48s)  sc-gateway-controller  exercises/log-ping-app-gateway
    Normal  SYNC    56s (x2 over 91s)    sc-gateway-controller  SYNC on exercises/log-ping-app-gateway was a success
  ```
- **Deploy HTTP-Routes for `ping-pong` application**
  ```bash
  kubectl apply -n exercises -f ping-pong/manifests/ping-pong-route.yaml  
  ```
  *Output*
  ```text
  httproute.gateway.networking.k8s.io/ping-pong-route created
  ```
- **Verify the `/pingpong` HTTPRoute includes the `URLRewrite` filter with `replacePrefixMatch`**
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
    Creation Timestamp:  2025-12-04T03:05:37Z
    Generation:          1
    Resource Version:    1764817537082863020
    UID:                 09c8dbbc-0316-4c2f-b9a9-065a4fac6437
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
      Filters:
        Type:  URLRewrite
        URL Rewrite:
          Path:
            Replace Prefix Match:  /
            Type:                  ReplacePrefixMatch
      Matches:
        Path:
          Type:   PathPrefix
          Value:  /pingpong
      Backend Refs:
        Group:
        Kind:    Service
        Name:    ping-pong-svc
        Port:    3456
        Weight:  1
      Matches:
        Path:
          Type:   PathPrefix
          Value:  /pings
  Events:
    Type    Reason  Age   From                   Message
    ----    ------  ----  ----                   -------
    Normal  ADD     15s   sc-gateway-controller  exercises/ping-pong-route
  ```
  > This output confirms that the HTTPRoute for the ping-pong app includes a URLRewrite filter configured to replace the prefix /pingpong with /, enabling the Gateway API rewrite functionality.

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
    Creation Timestamp:  2025-12-04T03:07:34Z
    Generation:          1
    Resource Version:    1764817654625023013
    UID:                 33b0a926-e3b9-43fc-abe4-01b606a5ca7c
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
        Port:    80
        Weight:  1
      Matches:
        Path:
          Type:   PathPrefix
          Value:  /
  Events:
    Type    Reason  Age   From                   Message
    ----    ------  ----  ----                   -------
    Normal  ADD     8s    sc-gateway-controller  exercises/log-output-route
  ```
- **Verify all 3 pods Running**
  ```bash
  kubectl get pods -n exercises -w  
  ```
  *Output*
  ```text
  NAME                              READY   STATUS    RESTARTS   AGE
  log-output-dep-86b9b9dd59-sm7rf   1/1     Running   0          13m
  ping-pong-dep-86dbc96667-d7457    1/1     Running   0          14m
  postgresql-db-0                   1/1     Running   0          16m
  postgresql-db-1                   1/1     Running   0          15m
  ```
- **Wait for GKE Gateway controller to fully set up the external load balancer**
  ```bash
  kubectl get gateway log-ping-app-gateway -n exercises -w
  ```
  **Output**
  ```text
  NAME                   CLASS                            ADDRESS       PROGRAMMED   AGE
  log-ping-app-gateway   gke-l7-global-external-managed   34.8.79.182   True         82s
  ```
  > Wait for `ADDRESS` to populate and `PROGRAMMED` to switch to True
- **Verify overall health of the configured entities**
  ```bash
  kubectl get all -n exercises
  ```
  ```text
  NAME                                  READY   STATUS    RESTARTS   AGE
  pod/log-output-dep-86b9b9dd59-sm7rf   1/1     Running   0          19m
  pod/ping-pong-dep-86dbc96667-d7457    1/1     Running   0          20m
  pod/postgresql-db-0                   1/1     Running   0          22m
  pod/postgresql-db-1                   1/1     Running   0          21m

  NAME                        TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
  service/log-output-svc      ClusterIP   34.118.237.247   <none>        80/TCP     19m
  service/ping-pong-svc       ClusterIP   34.118.235.8     <none>        3456/TCP   20m
  service/postgresql-db-svc   ClusterIP   None             <none>        5432/TCP   22m

  NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
  deployment.apps/log-output-dep   1/1     1            1           19m
  deployment.apps/ping-pong-dep    1/1     1            1           20m

  NAME                                        DESIRED   CURRENT   READY   AGE
  replicaset.apps/log-output-dep-86b9b9dd59   1         1         1       19m
  replicaset.apps/ping-pong-dep-86dbc96667    1         1         1       20m

  NAME                             READY   AGE
  statefulset.apps/postgresql-db   2/2     22m
  ```

### 4. Validate

  Use the Gateway Address (http://34.8.79.182/) to access the applications: 
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