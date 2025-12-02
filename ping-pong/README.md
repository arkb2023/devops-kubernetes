## Exercise 3.1. Pingpong GKE

Deploy Ping-pong application into GKE.

**Key Changes from Base**
- [`ping-pong/manifests/service.yaml`](./manifests/service.yaml) - Changed `type: ClusterIP` → `type: LoadBalancer`
- [`postgresql/postgresql-statefulset.yaml`](../postgresql/postgresql-statefulset.yaml) - Commented out `storageClassName: local-path`, letting GKE use default

- Base versions used:  
  - [Ping pong v2.7](https://github.com/arkb2023/devops-kubernetes/tree/2.7/ping-pong)  
  - [Docker image v2.7.2](https://hub.docker.com/repository/docker/arkb2023/ping-pong/tags/2.7.2)  

***


### 1. **Directory and File Structure**
<pre>
ping-pong/
├── Dockerfile
├── README.md
├── manifests
│   ├── deployment.yaml
│   ├── ingress.yaml
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

**Cluster Creation**:
```bash
gcloud container clusters create dwk-cluster
--zone=asia-south1-a
--cluster-version=1.32
--disk-size=32
--num-nodes=3
--machine-type=e2-micro
```
```bash
gcloud container clusters get-credentials dwk-cluster --zone=asia-south1-a
```
- **`project` namespace creation:**
```bash
kubectl create namespace exercises
```

***

### 3. **Deploy to Kubernetes**

**Apply PostgreSQL and ping-pong manifests**:  
```bash
kubectl apply -n exercises -f postgresql/
kubectl apply -n exercises -f ping-pong/manifests/
```


### 4. Validate

- **Verify PVCs bound successfully**:  
  ```bash
  kubectl get pvc -n exercises
  ```
  *Output*
  ```text
  NAME                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
  postgresql-db-disk-postgresql-db-0   Bound    pvc-b9c205ca-7398-41fc-a099-c942d53ca11d   1Gi        RWO            standard       <unset>                 19m
  postgresql-db-disk-postgresql-db-1   Bound    pvc-42d60e2e-6f94-438e-a3f4-04ff9e7b244c   1Gi        RWO            standard       <unset>                 13m
  ```

- **Verify all pods Running**:
  ```bash
  kubectl get pods -n exercises
  ```
  *Output*
  ```text
  NAME                             READY   STATUS    RESTARTS   AGE
  ping-pong-dep-6dd57fcf7f-fh8s8   1/1     Running   0          17m
  ping-pong-dep-cd4c69b85-xwkj9    1/1     Running   0          31s
  postgresql-db-0                  1/1     Running   0          20m
  postgresql-db-1                  1/1     Running   0          19m
  ```
- **Connect to Postgres to check data**
  ```bash
  kubectl exec -it -n exercises postgresql-db-0 -- bashsh
  ```
  *Output*
  ```text
  root@postgresql-db-0:/# psql -U testdbuser -d testdb
  psql (18.1 (Debian 18.1-1.pgdg13+2))
  Type "help" for help.

  testdb=#
  ```
- **Get initial value by hitting `/pings` HTTP endpoint:**  
  Verify the application response value matches the Postgres database value.  

  - Application returns `0`  
    ![caption](./images/01-initial-value-0.png)  
      

  - Database query confirms `0`:  
    ```bash
    testdb=# SELECT * FROM pingpong_counter;
    ```
    ```
    *Output:*  
    ```text
    id | value
    ----+-------
      1 |     0
    (1 row)
    ```

- **Hitting `/pingpong` HTTP endpoint increases the value by 1:**  
  Both the application response and Postgres database reflect the update.

  - Application returns `1`  
    ![caption](./images/02-pingpong1-value-1.png)  
      

  - Database query confirms `1`:  
    ```bash
    SELECT * FROM pingpong_counter;
    ```
    *Output:*  
    ```text
    id | value
    ----+-------
     1 |     1
    (1 row)
    ```

- **Hitting `/pingpong` a second time increases the value by 1:**  
  Both application and database show the increment.

  - Application returns `2`  
    ![caption](./images/03-pingpong2-value-2.png)  
      

  - Database query confirms `2`:  
    ```bash
    SELECT * FROM pingpong_counter;
    ```
    *Output:*  
    ```text
    id | value
    ----+-------
     1 |     2
    (1 row)
    ```

- **[DB persistence] Verify counter survives pod restart:**

  - Restart `ping-pong` deployment:  
    ```bash
    kubectl -n exercises rollout restart deployment ping-pong-dep
    ```
    *Output:*  
    ```text
    deployment.apps/ping-pong-dep restarted
    ```

  - Verify pod restart status:  
    ```bash
    kubectl -n exercises get pods
    ```
    *Output:*  
    ```text
    NAME                             READY   STATUS              RESTARTS   AGE
    ping-pong-dep-6dd57fcf7f-fh8s8   1/1     Running             0          17m
    ping-pong-dep-cd4c69b85-xwkj9    0/1     ContainerCreating   0          9s
    postgresql-db-0                  1/1     Running             0          19m
    postgresql-db-1                  1/1     Running             0          19m
    ping-pong-dep-cd4c69b85-xwkj9    1/1     Running             0          10s
    ```
    ```bash
    kubectl -n exercises get pods
    ```
    *Output:*  
    ```text
    NAME                           READY   STATUS    RESTARTS   AGE
    ping-pong-dep-6dd57fcf7f-fh8s8   1/1     Running   0          17m
    ping-pong-dep-cd4c69b85-xwkj9    1/1     Running   0          31s
    postgresql-db-0                  1/1     Running   0          20m
    postgresql-db-1                  1/1     Running   0          19m
    ```

  - `/pingpong` returns `pong: N+1` continuing from the previous value:  
    ![caption](./images/04-pingpong3-value-3-post-app-pod-restart.png)  
      

  - Database access confirms the same counter value:  
    ```bash
    SELECT * FROM pingpong_counter;
    ```
    *Output:*  
    ```text
    id | value
    ----+-------
     1 |     3
    (1 row)
    ```

***

### 6. **Cleanup**

**Delete Manifests** 
  ```bash
  kubectl delete -n exercises -f ping-pong/manifests/
  kubectl delete -n exercises -f postgresql/
  ```
  
**Stop the k3d Cluster**  
```bash
gcloud container clusters delete dwk-cluster --zone=asia-south1-a
```
*Output*
```text
The following clusters will be deleted.
 - [dwk-cluster] in [asia-south1-a]

Do you want to continue (Y/n)?  Y

Deleting cluster dwk-cluster...done.
Deleted [https://container.googleapis.com/v1/projects/dwk-gke-480015/zones/asia-south1-a/clusters/dwk-cluster].
```

---


<!--
check logs
kubectl -n exercises logs postgresql-db-1 -c postgresql-db
kubectl -n exercises logs postgresql-db-0 -c postgresql-db 
# live logs
kubectl -n exercises logs -f postgresql-db-1
-->