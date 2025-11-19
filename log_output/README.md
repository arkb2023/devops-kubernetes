## Log output app

### 1. Initialize Kubernetes cluster

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

### 2. Create the Log script and Dockerfile  
- Refer [log_output.sh](./log_output.sh) 
- Refer [Dockerfile](./Dockerfile)

---

### 3. Build and Test locally
    
**Build**
```bash
docker build  -t arkb2023/log-output:latest .
```
```Output
[+] Building 2.1s (10/10) FINISHED                                                                                                                                                                docker:default
=> [internal] load build definition from Dockerfile                                                                                                                                                        0.0s
=> => transferring dockerfile: 221B                                                                                                                                                                        0.0s
=> [internal] load metadata for docker.io/library/alpine:latest                                                                                                                                            1.7s
=> [auth] library/alpine:pull token for registry-1.docker.io                                                                                                                                               0.0s
=> [internal] load .dockerignore                                                                                                                                                                           0.0s
=> => transferring context: 2B                                                                                                                                                                             0.0s
=> [1/4] FROM docker.io/library/alpine:latest@sha256:4b7ce07002c69e8f3d704a9c5d6fd3053be500b7f1c69fc0d80990c2ad8dd412                                                                                      0.0s
=> => resolve docker.io/library/alpine:latest@sha256:4b7ce07002c69e8f3d704a9c5d6fd3053be500b7f1c69fc0d80990c2ad8dd412                                                                                      0.0s
=> [internal] load build context                                                                                                                                                                           0.0s
=> => transferring context: 35B                                                                                                                                                                            0.0s
=> CACHED [2/4] RUN apk add --no-cache bash                                                                                                                                                                0.0s
=> CACHED [3/4] WORKDIR /usr/src/app                                                                                                                                                                       0.0s
=> CACHED [4/4] COPY log_output.sh .                                                                                                                                                                       0.0s
=> exporting to image                                                                                                                                                                                      0.2s
=> => exporting layers                                                                                                                                                                                     0.0s
=> => exporting manifest sha256:03d5c711cf769518fa58d5df58fdd70fbfced94d5cb87c71224cc98e92a39067                                                                                                           0.0s
=> => exporting config sha256:c2fa8e569df0bdd9eb7a6cff0924a65d4e06b239547444adb456851a5ef803ff                                                                                                             0.0s
=> => exporting attestation manifest sha256:398f45b796f8884fa1c283ff8ef8fcefabae82cdd8417a02d89003c70971e3d5                                                                                               0.0s
=> => exporting manifest list sha256:ffa1f5b74bd37a9171ef549711988ff05faabb2f221dcfb0db55d59db0a778c7                                                                                                      0.0s
=> => naming to docker.io/arkb2023/log-output:latest                                                                                                                                                       0.0s
=> => unpacking to docker.io/arkb2023/log-output:latest                                                                                                                                                    0.1s
```
**Test**
```bash
docker run --rm arkb2023/log-output:latest
```
```Output
2025-11-18T13:53:21+00:00: 9f4b98a0-c7f9-4e82-aef9-d08e3e496bb4
2025-11-18T13:53:26+00:00: 9f4b98a0-c7f9-4e82-aef9-d08e3e496bb4
2025-11-18T13:53:31+00:00: 9f4b98a0-c7f9-4e82-aef9-d08e3e496bb4
```

---

### 4. Push image to DockerHub
```
docker push arkb2023/log-output:latest
```
```Output
The push refers to repository [docker.io/arkb2023/log-output]
5f0c0a7e0a6d: Pushed
9d9447ba22ec: Pushed
2d35ebdb57d9: Pushed
717cbf23939e: Pushed
45d26deecfe2: Pushed
latest: digest: sha256:ffa1f5b74bd37a9171ef549711988ff05faabb2f221dcfb0db55d59db0a778c7 size: 856
```
> The image is published at:
https://hub.docker.com/repository/docker/arkb2023/log-output/tags/latest

---

### 5. Create Kubernetes Manifests
- Refer [deployment.yaml](./manifests/deployment.yaml)
> In deployment.yaml, register the DockerHub repo image `arkb2023/log-output:latest`

---

### 6. Deploy and Verify the App

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
log-output-dep      1/1     1            1           21m
```

```bash
kubectl get pods
```
```Output
NAME                                 READY   STATUS    RESTARTS   AGE
log-output-dep-68fc9c9b54-v54qw      1/1     Running   0          23m
```

**Verify logs**
```bash
kubectl logs -f log-output-dep-68fc9c9b54-v54qw
```
```Output
2025-11-18T13:57:58+00:00: cf35e8ec-be2d-4571-bf2a-710477b78348
2025-11-18T13:58:03+00:00: cf35e8ec-be2d-4571-bf2a-710477b78348
2025-11-18T13:58:08+00:00: cf35e8ec-be2d-4571-bf2a-710477b78348
```

---