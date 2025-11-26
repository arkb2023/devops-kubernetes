## Exercise: 2.4. The project, step 9

Create a namespace called `project` for the [project](../the_project/) and move everything related to the project to that namespace. Use the new namespace in the future for all the project related exercises.

### Resource Updates  
- **todo_app** manifests updated with `namespace: project`:  
  - [deployment.yaml](./todo_app/manifests/deployment.yaml)  
  - [service.yaml](./todo_app/manifests/service.yaml)  
  - [ingress.yaml](./todo_app/manifests/ingress.yaml)  
- **todo backend** manifests updated with `namespace: project`:  
  - [deployment.yaml](./todo_backend/manifests/deployment.yaml)  
  - [service.yaml](./todo_backend/manifests/service.yaml)  
  - [ingress.yaml](./todo_backend/manifests/ingress.yaml)  
- **Volumes** manifests updated with `namespace: project`:  
  - [PersistentVolume](../volumes/persistentvolume.yaml)
  - [PersistentVolumeClaim](../volumes/persistentvolumeclaim.yaml)

1. **Create the `project` namespace:**

```bash
kubectl create namespace project
```

2. **Deploy the project resources into the `project` namespace:**

```bash
kubectl apply -n project \
  -f the_project/todo_app/manifests/ \
  -f the_project/todo_backend/manifests/ \
  -f volumes/
```
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
4. **Verify deployments and services are correctly running in the `project` namespace:**

```bash
kubectl get all -n project
```
```text
NAME                                    READY   STATUS    RESTARTS   AGE
pod/todo-app-dep-7d7b7b7db-c7gv8        1/1     Running   0          48s
pod/todo-backend-dep-575c756bb8-kw9g2   1/1     Running   0          48s

NAME                       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
service/todo-app-svc       ClusterIP   10.43.71.75    <none>        1234/TCP   48s
service/todo-backend-svc   ClusterIP   10.43.40.193   <none>        4567/TCP   48s

NAME                               READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/todo-app-dep       1/1     1            1           48s
deployment.apps/todo-backend-dep   1/1     1            1           48s

NAME                                          DESIRED   CURRENT   READY   AGE
replicaset.apps/todo-app-dep-7d7b7b7db        1         1         1       48s
replicaset.apps/todo-backend-dep-575c756bb8   1         1         1       48s
```

***
