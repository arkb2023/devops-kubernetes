## Exercise: 1.6. The project, step 4
### Todo App Server Enhancements

- Built upon the application from [Exercise: 1.5. The project, step 3](https://github.com/arkb2023/devops-kubernetes/tree/1.5/the_project)
- Implemented NodePort service configuration [service.yaml](./todo-app/manifests/service.yaml) to enable external access to the Todo App server.

### 1. **Directory and File Structure**
```
the_project
├── README.md
└── todo-app
    ├── Dockerfile
    ├── main.py
    └── manifests
        ├── deployment.yaml
        └── service.yaml
```

***

### 2. Prerequisites
- `Docker` `k3d` `kubectl` installed and `k3s-default` cluster running via `k3d`

> Used Docker image is published at:
https://hub.docker.com/repository/docker/arkb2023/todo-app/tags/1.6.2

***

### 3. Deploy to Kubernetes

**Creates a cluster**

```bash
k3d cluster create --port 8082:30080@agent:0 -port 8081:80@loadbalancer --agents 2
```
Where,  

`--port 8082:30080@agent:0`: Exposes host port 8082 mapped to port 30080 on the first agent node, allowing access through `localhost:8082`.

`-port 8081:80@loadbalancer`: Exposes host port 8081 mapped to the load balancer's port 80.

**Setup the deployment resource:**
```bash
kubectl apply -f manifests/deployment.yaml
```
**Setup the service resource:**
```bash
kubectl apply -f manifests/service.yaml
```
**Ensure the pod is running and ready:**
```bash
kubectl get pods
```
*Output*
```text
NAME                            READY   STATUS        RESTARTS   AGE
todo-app-dep-687cc89674-97k97   1/1     Running       0          23s
```

**Verify service is accessible inside the cluster**

```bash
kubectl get service|egrep "todo|PORT"
```
*Output*
```text
NAME           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
todo-app-svc   NodePort    10.43.139.174   <none>        1234:30080/TCP   133m
```
**Inspect Pod Logs for Application Readiness**
```bash
kubectl logs -f todo-app-dep-687cc89674-97k97
```
*Output*
```text
INFO:     Started server process [7]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)
Starting app on port 3000...
App mode: Production
Application hash: 1789327b
INFO:     10.42.0.0:54792 - "GET / HTTP/1.1" 200 OK
```

***

### 5. Verify Application Response 

- Browser access via `http://localhost:8082`
![Browser view](./images/01-browser-access-on-8082.png) 


### 5. **Cleanup**

```bash
kubectl delete -f manifests/service.yaml
kubectl delete -f manifests/deployment.yaml
k3d cluster delete
```
***