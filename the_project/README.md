## Todo App Server

### 1. **Directory and File Structure**
```
the_project/
└── todo-app/
    ├── Dockerfile
    ├── README.md
    ├── main.py
    └── manifests/
        └── deployment.yaml
```

***

### 2. Prerequisites
- Docker, k3d, kubectl installed

***

### 3. **Build, Test & Push Docker Image**

**Build**
```bash
docker build -t arkb2023/todo-app:latest .
```
**Run**
```bash
docker run -d --rm -e PORT=8080 -p 8080:8080 arkb2023/todo-app:latest
```
*Output*
```
7aa9421ddd9b9d1a7f2671d136df7dbe073cd39d892b698f4bff8ec2a4cf245e
```
**Health check**
```bash
docker ps |egrep "todo|PORT"
```
```
CONTAINER ID   IMAGE                            COMMAND                  CREATED          STATUS          PORTS                                         NAMES
7aa9421ddd9b   arkb2023/todo-app:latest         "sh -c 'uvicorn main…"   6 minutes ago    Up 6 minutes    0.0.0.0:8080->8080/tcp, [::]:8080->8080/tcp   sweet_heyrovsky
```
**Test**
```bash
http GET http://localhost:8080/
```
*Output*
```text
HTTP/1.1 200 OK
content-length: 41
content-type: application/json
date: Wed, 19 Nov 2025 05:09:16 GMT
server: uvicorn

{
    "message": "Server started in port 8080"
}
```
**Check container logs**
```bash
docker logs -f sweet_heyrovsky
```
*Output*
```text
INFO:     Started server process [7]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     172.17.0.1:34700 - "GET / HTTP/1.1" 200 OK
```

**Push Docker Image**
```bash
docker push arkb2023/todo-app:latest
```
*Output*
```text
The push refers to repository [docker.io/arkb2023/todo-app]
0e4bc2bd6656: Pushed
e90b7e24c8b4: Pushed
22b63e76fde1: Pushed
1771569cc129: Pushed
b3dd773c3296: Pushed
6089e529749f: Pushed
aeb69cd30fad: Pushed
0c1aa45fead9: Pushed
latest: digest: sha256:2615eebda32728e86ff57c9da3d3ab0cbddea37c5c091856baf1d70cec11b8bf size: 856
```
> The image is published at:
https://hub.docker.com/repository/docker/arkb2023/todo-app/tags/latest

***

### 4. **Deploy to Kubernetes**

**Start the k3d Cluster**
```bash
k3d cluster start k3s-default
```
*Output*
```text
INFO[0000] Using the k3d-tools node to gather environment information
INFO[0000] Starting existing tools node k3d-k3s-default-tools...
INFO[0000] Starting node 'k3d-k3s-default-tools'
INFO[0001] Starting new tools node...
INFO[0001] Starting node 'k3d-k3s-default-tools'
INFO[0002] Starting cluster 'k3s-default'
INFO[0002] All servers already running.
INFO[0002] All agents already running.
INFO[0002] Starting helpers...
INFO[0002] Starting node 'k3d-k3s-default-tools'
INFO[0002] Started cluster 'k3s-default'
```
**Apply the Deployment Manifest**
```bash
kubectl apply -f manifests/deployment.yaml
```
*Output*
```text
deployment.apps/todo-app created
```
**Verify Created deployment**
```bash
kubectl get deployments
```
*Output*
```text
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
todo-app   1/1     1            1           72m
```
**Verify Pod Running Status**
```bash
kubectl get pods
```
*Output*
```text
NAME                       READY   STATUS    RESTARTS   AGE
todo-app-dccc58cb4-c42hd   1/1     Running   0          26s
```

**Verify pod logs for app readiness status**
```bash
kubectl logs -f todo-app-dccc58cb4-c42hd
```
*Output*
```text
INFO:     Started server process [8]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### 5. **Cleanup**
**Delete the Kubernetes Deployment**
```bash
kubectl delete deployment todo-app
```
*Output*
```text
deployment.apps "todo-app" deleted from default namespace
```
**Stop the k3d Cluster**
```bash
k3d cluster stop k3s-default
```
*Output*
```text
INFO[0000] Stopping cluster 'k3s-default'
INFO[0012] Stopped cluster 'k3s-default'
```

***