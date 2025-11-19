## Log output app *(with manifests)*

### 1. **Directory and File Structure**
<pre>
.
├── Dockerfile
├── README.md
├── log_output.sh
└── manifests
    └── deployment.yaml
</pre>

***

### 2. Prerequisites
- Docker, k3d, kubectl installed

### 3. Build and Test locally
- Follow the steps described in [Exercise 1.1 README](https://github.com/arkb2023/devops-kubernetes/blob/1.1/log_output/README.md)

### 4. Push image to DockerHub
- Follow the steps described in [Exercise 1.1 README](https://github.com/arkb2023/devops-kubernetes/blob/1.1/log_output/README.md)

---

### 5. **Deploy to Kubernetes**

**Start the k3d Cluster**
```bash
k3d cluster start
```
```Output
INFO[0000] Using the k3d-tools node to gather environment information
INFO[0000] Starting existing tools node k3d-k3s-default-tools...
INFO[0000] Starting node 'k3d-k3s-default-tools'
INFO[0000] Starting new tools node...
INFO[0000] Starting node 'k3d-k3s-default-tools'
INFO[0002] Starting cluster 'k3s-default'
INFO[0002] Starting servers...
INFO[0002] Starting node 'k3d-k3s-default-server-0'
INFO[0009] Starting agents...
INFO[0009] Starting node 'k3d-k3s-default-agent-1'
INFO[0009] Starting node 'k3d-k3s-default-agent-0'
INFO[0012] Starting helpers...
INFO[0012] Starting node 'k3d-k3s-default-tools'
INFO[0012] Starting node 'k3d-k3s-default-serverlb'
INFO[0018] Injecting records for hostAliases (incl. host.k3d.internal) and for 5 network members into CoreDNS configmap...
INFO[0021] Started cluster 'k3s-default'
```

**Check the running containers**
```bash
docker ps
```
```Output
CONTAINER ID   IMAGE                            COMMAND                  CREATED         STATUS         PORTS                     NAMES
511018adc2e4   ghcr.io/k3d-io/k3d-tools:5.8.3   "/app/k3d-tools noop"    4 minutes ago   Up 4 minutes                             k3d-k3s-default-tools
baafad67dc35   ghcr.io/k3d-io/k3d-proxy:5.8.3   "/bin/sh -c nginx-pr…"   4 hours ago     Up 3 minutes   0.0.0.0:37263->6443/tcp   k3d-k3s-default-serverlb
e958a8608497   rancher/k3s:v1.31.5-k3s1         "/bin/k3d-entrypoint…"   4 hours ago     Up 3 minutes                             k3d-k3s-default-agent-1
cdd430d6ba86   rancher/k3s:v1.31.5-k3s1         "/bin/k3d-entrypoint…"   4 hours ago     Up 3 minutes                             k3d-k3s-default-agent-0
4a99bd2617c1   rancher/k3s:v1.31.5-k3s1         "/bin/k3d-entrypoint…"   4 hours ago     Up 4 minutes                             k3d-k3s-default-server-0
```

---

**Apply the Deployment Manifest**
- Refer deployment manifest: [deployment.yaml](./manifests/deployment.yaml)
  > In deployment.yaml, register the DockerHub repo image `arkb2023/log-output:latest`

```bash
kubectl apply -f manifests/deployment.yaml
```
```Output
deployment.apps/log-output-dep created
```

**Check deployments**
```bash
kubectl get deployments
```
```Output
NAME                READY   UP-TO-DATE   AVAILABLE   AGE
log-output-dep      1/1     1            1           18s
```

```bash
kubectl get pods
```
```Output
NAME                                 READY   STATUS    RESTARTS   AGE
textlog-output-dep-66b86f6d8b-q9fwg      1/1     Running   0          24s
```

**Verify logs**
```bash
kubectl logs -f textlog-output-dep-66b86f6d8b-q9fwg
```
```Output
2025-11-19T09:00:26+00:00: 9106198b-8e35-4eea-9a5b-e6376bda92d8
2025-11-19T09:00:31+00:00: 9106198b-8e35-4eea-9a5b-e6376bda92d8
2025-11-19T09:00:36+00:00: 9106198b-8e35-4eea-9a5b-e6376bda92d8
```


### 6. **Cleanup**
**Delete the Kubernetes Deployment**
```bash
kubectl delete deployment log-output-dep
```
*Output*
```text
deployment.apps "log-output-dep" deleted from default namespace
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

---