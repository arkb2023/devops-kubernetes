## Exercise 3.5: The project, step 14

**Objective**: Configure the project to use Kustomize, and deploy it to Google Kubernetes Engine.

**Key Changes from Base**  
The deployment uses a layered Kustomize structure for the project, managing multi-resource Kubernetes applications with environment overlays.

- **[`apps/the-project/kustomization.yaml`](../apps/the-project/kustomization.yaml):** This file consolidates all core application manifests for the `project` namespace, consisting of:

  - PostgreSQL StatefulSet and supporting ConfigMaps/Secrets:  
    - [`postgres-db-secret.yaml`](../apps/the-project/postgres-db-secret.yaml)
    - [`postgresql-configmap.yaml`](../apps/the-project/postgresql-configmap.yaml)
    - [`postgresql-service.yaml`](../apps/the-project/postgresql-service.yaml)
    - [`postgresql-statefulset.yaml`](../apps/the-project/postgresql-statefulset.yaml)
  - Todo Application Deployment and Service:  
    - [`todo-app-deployment.yaml`](../apps/the-project/todo-app-deployment.yaml)
    - [`todo-app-service.yaml`](../apps/the-project/todo-app-service.yaml)
  - Todo Backend Application Deployment and Service:  
    - [`todo-backend-deployment.yaml`](../apps/the-project/todo-backend-deployment.yaml)
    - [`todo-backend-service.yaml`](../apps/the-project/todo-backend-service.yaml)
  - Application ConfigMap:  
    - [`project-configmap.yaml`](../apps/the-project/project-configmap.yaml)
  - Wiki Todo Generator - CronJob:  
    - [`cron_wiki_todo.yaml`](../apps/the-project/cron_wiki_todo.yaml)

- **[`environments/project-gke/kustomization.yaml`](../environments/project-gke/kustomization.yaml):**  This higher-level overlay manages GKE-specific configurations and environment declarations. It references:
  - [`namespace.yaml`](../environments/project-gke/namespace.yaml) — creates the `project` namespace.
  - [`persistentvolumeclaim.yaml`](../environments/project-gke/persistentvolumeclaim.yaml) — GKE dynamic PVC request using the default `standard-rwo` StorageClass.
  - [`gateway.yaml`](../environments/project-gke/gateway.yaml) — Gateway API resource defining GKE L7 external HTTP traffic routing.
  - HTTPRoute manifests:
    - [`todo-app-route.yaml`](../environments/project-gke/todo-app-route.yaml)
    - [`todo-backend-route.yaml`](../environments/project-gke/todo-backend-route.yaml)

- This enables a single command deploy `kubectl apply -k environments/project-gke` that provisions the full application stack.

***

**Base Application Versions**
- [Toto App and Todo Backend App v2.10](https://github.com/arkb2023/devops-kubernetes/tree/2.10/the_project/)

### 1. **Directory and File Structure**
<pre>

  # kustomization: Common Project resource yamls 
  apps/the-project/
  ├── cron_wiki_todo.yaml
  ├── kustomization.yaml
  ├── postgres-db-secret.yaml
  ├── postgresql-configmap.yaml
  ├── postgresql-service.yaml
  ├── postgresql-statefulset.yaml
  ├── project-configmap.yaml
  ├── todo-app-deployment.yaml
  ├── todo-app-service.yaml
  ├── todo-backend-deployment.yaml
  └── todo-backend-service.yaml

  # kustomization: GKE Project resource yamls 
  environments/project-gke/
  ├── gateway.yaml
  ├── kustomization.yaml
  ├── namespace.yaml
  ├── persistentvolumeclaim.yaml
  ├── todo-app-route.yaml
  └── todo-backend-route.yaml

  # Todo App 
  the_project/todo_app/
  ├── Dockerfile
  ├── app
  │   ├── __init__.py
  │   ├── cache.py
  │   ├── main.py
  │   ├── routes
  │   │   ├── __init__.py
  │   │   └── frontend.py
  │   ├── static
  │   │   └── scripts.js
  │   └── templates
  │       └── index.html

  # Todo Backend App 
  the_project/todo_backend/
  ├── Dockerfile
  ├── app
  │   ├── __init__.py
  │   ├── main.py
  │   ├── models.py
  │   ├── routes
  │   │   ├── __init__.py
  │   │   └── todos.py
  │   └── storage.py
  ├── docker-compose.yml
  └── wait-for-it.sh

  # Wiki Todo Generator CronJob
  the_project/cronjob/
  ├── Dockerfile
  └── cron_wiki_todo.py

</pre>


### 2. Prerequisites (GCP/GKE)

- Google Cloud CLI (`gcloud`) updated to 548.0.0
- kubectl with `gke-gcloud-auth-plugin`
- GCP Project: `dwk-gke-480015` configured
- Cluster Creation:
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
- Fetch and configure Kubernetes cluster access credentials locally, enabling kubectl to authenticate and manage the specified GKE cluster  
  ```bash
  gcloud container clusters get-credentials dwk-cluster --zone=asia-south1-a
  ```
- Namespace creation:
  ```bash
  kubectl create namespace project
  ```


### 3. Docker Image Build & Push
```
cd the-project/todo-app
docker build -t arkb2023/todo-backend:3.5.1 .
docker push arkb2023/todo-backend:3.5.1

cd the-project/todo-app
docker build -t arkb2023/todo-app:3.5.1 .
docker push arkb2023/todo-app:3.5.1
```
> Docker images are published at:  
https://hub.docker.com/repository/docker/arkb2023/todo-backend/tags/3.5.1  
https://hub.docker.com/repository/docker/arkb2023/todo-app/tags/3.5.1  



### 4. **Deploy to Kubernetes**

- **Deploy with kustomize**:  
  ```bash
  kubectl apply -k environments/project-gke/
  ```
  ```text
  namespace/project configured
  configmap/postgres-db-config created
  configmap/project-config-env created
  secret/postgres-db-secret created
  service/postgresql-db-svc created
  service/todo-app-svc created
  service/todo-backend-svc created
  persistentvolumeclaim/local-pv-claim created
  deployment.apps/todo-app-dep created
  deployment.apps/todo-backend-dep created
  statefulset.apps/postgresql-db created
  cronjob.batch/wiki-todo-generator created
  gateway.gateway.networking.k8s.io/project-gateway created
  httproute.gateway.networking.k8s.io/todo-app-route created
  httproute.gateway.networking.k8s.io/todo-backend-route created
  ```

- **Verify overall health of the configured entities**
  ```bash
  kubectl get all -n project
  ```
  ```text
  NAME                                    READY   STATUS    RESTARTS   AGE
  pod/postgresql-db-0                     1/1     Running   0          25m
  pod/todo-app-dep-64d5554c8d-8994k       1/1     Running   0          3m1s
  pod/todo-backend-dep-5f77c88d4c-rnccp   1/1     Running   0          2m53s

  NAME                        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
  service/postgresql-db-svc   ClusterIP   None            <none>        5432/TCP   25m
  service/todo-app-svc        ClusterIP   34.118.234.89   <none>        1234/TCP   25m
  service/todo-backend-svc    ClusterIP   34.118.237.91   <none>        4567/TCP   25m

  NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
  deployment.apps/todo-app-dep       1/1     1            1           25m
  deployment.apps/todo-backend-dep   1/1     1            1           25m

  NAME                                          DESIRED   CURRENT   READY   AGE
  replicaset.apps/todo-app-dep-64d5554c8d       1         1         1       12m
  replicaset.apps/todo-app-dep-777499b97f       0         0         0       25m
  replicaset.apps/todo-backend-dep-5f77c88d4c   1         1         1       12m
  replicaset.apps/todo-backend-dep-955f76f94    0         0         0       25m

  NAME                             READY   AGE
  statefulset.apps/postgresql-db   1/1     25m

  NAME                                SCHEDULE    TIMEZONE   SUSPEND   ACTIVE   LAST SCHEDULE   AGE
  cronjob.batch/wiki-todo-generator   0 * * * *   <none>     False     0        <none>          25m
  ```

- **Wait for GKE Gateway controller to fully set up the external load balancer**
  ```bash
  kubectl get gateway project-gateway -n project
  ```
  **Output**
  ```text
  NAME              CLASS                            ADDRESS          PROGRAMMED   AGE
  project-gateway   gke-l7-global-external-managed   35.244.202.196   True         25m
  ```
  > Wait for `ADDRESS` to populate and `PROGRAMMED` to switch to True

### 4. Validate
  Use the Gateway Address `http://35.244.202.196` to access the application: 
- Test Todo App response on `/` HTTP endpoint:  

  - Application returns the expected response  
    ![caption](./images/01-initial-page.png)  

- Test Todo Creation:  

  - Application shows the created todo item in response    
    ![caption](./images/02-post-todo-task-success.png)
      


## 8. Cleanup

**Delete all project resources (Kustomize)**
```bash
kubectl delete -k environments/project-gke
```
**Delete GKE cluster**
```bash
gcloud container clusters delete dwk-cluster \
  --zone=asia-south1-a \
  --quiet
```