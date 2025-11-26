## Exercise 2.3: Keep Them Separated

### Summary
- Deploy the `ping-pong` and `log-output` applications within the `exercises` namespace.  
- Continue deploying the `todo-app` and `todo-backend` applications in the `default` namespace.

### Resource Updates  
- **Log Output** manifests updated with `namespace: exercises`:  
  - [deployment.yaml](./log_output/manifests/deployment.yaml)  
  - [service.yaml](./log_output/manifests/service.yaml)  
  - [ingress.yaml](./log_output/manifests/ingress.yaml)  
- **Ping Pong** manifests updated with `namespace: exercises`:  
  - [deployment.yaml](./ping-pong/manifests/deployment.yaml)  
  - [service.yaml](./ping-pong/manifests/service.yaml)  
  - [ingress.yaml](./ping-pong/manifests/ingress.yaml)  
- Manifests for `todo-app`, `todo-backend`, `PersistentVolume`, and `PersistentVolumeClaim` remain unchanged to retain deployment in the `default` namespace.

### Validation Coverage  
- Namespace creation and confirmation.  
- Application deployment in their respective namespaces (`exercises` and `default`).  
- Verification of deployments and namespace isolation.

***

### 2. Prerequisites

- Ensure the following tools are installed:
  - Docker  
  - k3d (K3s in Docker)  
  - kubectl (Kubernetes CLI)
- Create and run a Kubernetes cluster with k3d, using 2 agent nodes and port mapping to expose the ingress load balancer on host port 8081:
    ```bash
    k3d cluster create mycluster --agents 2 --port 8081:80@loadbalancer
    ```
***


### Step 1: Create the required namespace for exercises

```bash
kubectl create namespace exercises
```

***

### Step 2: Deploy **ping-pong** and **log-output** apps in the `exercises` namespace

```bash
kubectl apply -n exercises \
    -f ping-pong/manifests/ \
    -f log_output/manifests/
```

Expected output:
```text
deployment.apps/ping-pong-dep created
ingress.networking.k8s.io/dwk-ping-pong-ingress created
service/ping-pong-svc created
deployment.apps/log-output-dep created
ingress.networking.k8s.io/dwk-log-output-ingress created
service/log-output-svc created
```

Verify pods:
```bash
kubectl get pods -n exercises
```

Sample output:
```text
NAME                             READY   STATUS              RESTARTS   AGE
log-output-dep-b6f7bdc-7qgth     0/1     ContainerCreating   0          8s
ping-pong-dep-57d7c4b697-xsc6h   1/1     Running            0          30s
```

Verify services:
```bash
kubectl get svc -n exercises
```

Sample output:
```text
NAME             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
log-output-svc   ClusterIP   10.43.79.151    <none>        2345/TCP    18s
ping-pong-svc    ClusterIP   10.43.91.58     <none>        3456/TCP    40s
```

Wait a few seconds and check pods again:
```bash
kubectl get pods -n exercises
```

Expected pods running:
```text
NAME                             READY   STATUS    RESTARTS   AGE
log-output-dep-b6f7bdc-7qgth     1/1     Running   0          34s
ping-pong-dep-57d7c4b697-xsc6h   1/1     Running   0          56s
```

***

### Step 4: Deploy **todo app** and **todo-backend** in the `default` namespace

```bash
kubectl apply \
    -f the_project/todo_app/manifests/ \
    -f the_project/todo_backend/manifests/ \
    -f volumes/
```

Expected output:
```text
deployment.apps/todo-app-dep created
ingress.networking.k8s.io/todo-app-ingress created
service/todo-app-svc created
deployment.apps/todo-backend-dep created
ingress.networking.k8s.io/todo-backend-ingress created
service/todo-backend-svc created
persistentvolume/local-pv created
persistentvolumeclaim/local-pv-claim created
```

Verify pods in `default`:

```bash
kubectl get pods
```

Sample output:
```text
NAME                             READY   STATUS    RESTARTS      AGE
todo-app-dep-5cd4f9456c-xsjrs    1/1     Running   1 (16m ago)   9h
todo-backend-dep-745ddccd-d78jc  1/1     Running   1 (16m ago)   10h
```

Verify services:

```bash
kubectl get svc
```

Sample output:
```text
NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
kubernetes         ClusterIP   10.43.0.1       <none>        443/TCP     10h
todo-app-svc       ClusterIP   10.43.187.35    <none>        1234/TCP    10h
todo-backend-svc   ClusterIP   10.43.54.232    <none>        4567/TCP    10h
```

Verify ingresses:

```bash
kubectl get ing
```

Sample output:
```text
NAME                  CLASS    HOSTS   ADDRESS                       PORTS   AGE
todo-app-ingress      <none>   *       172.18.0.2,172.18.0.3,172.18.0.4 80     10h
todo-backend-ingress  <none>   *       172.18.0.2,172.18.0.3,172.18.0.4 80     10h
```

***

### Step 6: Check deployments and pods per namespace

Check `exercises` namespace:

```bash
kubectl get all -n exercises
```

Sample output:
```text
NAME                                 READY   STATUS    RESTARTS   AGE
pod/log-output-dep-b6f7bdc-7qgth     1/1     Running   0          119s
pod/ping-pong-dep-57d7c4b697-xsc6h   1/1     Running   0          2m21s

NAME                               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
service/log-output-svc             ClusterIP   10.43.79.151    <none>        2345/TCP    119s
service/ping-pong-svc              ClusterIP   10.43.91.58     <none>        3456/TCP    2m21s

NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/log-output-dep   1/1     1            1           119s
deployment.apps/ping-pong-dep    1/1     1            1           2m21s

NAME                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/log-output-dep-b6f7bdc   1         1         1       119s
replicaset.apps/ping-pong-dep-57d7c4b697 1         1         1       2m21s
```

Check `default` namespace:

```bash
kubectl get all -n default
```

Sample output:
```text
NAME                                READY   STATUS    RESTARTS      AGE
pod/todo-app-dep-5cd4f9456c-xsjrs   1/1     Running   1 (17m ago)   9h
pod/todo-backend-dep-745ddccd-d78jc 1/1     Running   1 (17m ago)   10h

NAME                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)     AGE
service/kubernetes                ClusterIP   10.43.0.1       <none>        443/TCP     10h
service/todo-app-svc             ClusterIP   10.43.187.35    <none>        1234/TCP    10h
service/todo-backend-svc         ClusterIP   10.43.54.232    <none>        4567/TCP    10h

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/todo-app-dep       1/1     1           1           10h
deployment.apps/todo-backend-dep   1/1     1           1           10h

NAME                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/todo-app-dep-5cd4f9456c  1         1         1       9h
replicaset.apps/todo-backend-dep-745ddccd 1        1         1       10h
```

***

### Confirm namespace in pod details

```bash
kubectl get pods --all-namespaces
```

Sample output:
```text
NAMESPACE    NAME                                READY   STATUS    RESTARTS     AGE
default      todo-app-dep-5cd4f9456c-xsjrs      1/1     Running   1 (17m ago)  9h
default      todo-backend-dep-745ddccd-d78jc    1/1     Running   1 (17m ago)  10h
exercises    log-output-dep-b6f7bdc-7qgth       1/1     Running   0            2m29s
exercises    ping-pong-dep-57d7c4b697-xsc6h     1/1     Running   0            2m51s
kube-system  coredns-ccb96694c-jb52t             1/1     Running   1 (17m ago)  10h
...
```

***

### Cleanup: Delete all resources from `exercises` namespace

```bash
kubectl delete all --all -n exercises
```

Sample output:

```text
pod "log-output-dep-b6f7bdc-7qgth" deleted from exercises namespace
pod "ping-pong-dep-57d7c4b697-xsc6h" deleted from exercises namespace
service "log-output-svc" deleted from exercises namespace
service "ping-pong-svc" deleted from exercises namespace
deployment.apps "log-output-dep" deleted from exercises namespace
deployment.apps "ping-pong-dep" deleted from exercises namespace
```

***

### Cleanup: Delete all resources from `default` namespace

```bash
kubectl delete all --all -n default
```

Sample output:

```text
pod "todo-app-dep-5cd4f9456c-xsjrs" deleted from default namespace
pod "todo-backend-dep-745ddccd-d78jc" deleted from default namespace
service "kubernetes" deleted from default namespace
service "todo-app-svc" deleted from default namespace
service "todo-backend-svc" deleted from default namespace
deployment.apps "todo-app-dep" deleted from default namespace
deployment.apps "todo-backend-dep" deleted from default namespace
replicaset.apps "todo-app-dep-7d7b7b7db" deleted from default namespace
```

***
