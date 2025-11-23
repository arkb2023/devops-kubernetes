## Exercise 1.11. Persisting data  
### `Log output` and `Ping pong` applications enhanced to share data using persistent volume. 

**Volume Resources**
- Added `Persistent Volume` and `Persistent Volume Claim` configuration files:
  - [PersistentVolume](../volumes/persistentvolume.yaml)
  - [PersistentVolumeClaim](../volumes/persistentvolumeclaim.yaml)

**Application Updates**
- Enhanced `Log Output` application [deployment.yaml](../log_output/manifests/deployment.yaml) resource to mount PVC into `Log output` container 
- Enhanced `Ping Pong` application [deployment.yaml](./manifests/deployment.yaml) resource to mount the same PVC into `Ping pong` container 
- Added `Ping Pong` application [ingress](./manifests/ingress.yaml) resource to route requests with path prefix `/pingpong` to the `ping-pong-svc` service on port `3456`.

**Application Functionality**
- `Ping pong` application: On each request, increments the request count and writes it to a shared file `/usr/src/app/files/pingpong-requests.txt`
- `Log output` application: On each request, reads the content of the shared file `/usr/src/app/files/pingpong-requests.txt`, generates a `timestamp` and a `random string`, and combines all information in the HTTP response.
- Base application versions used:
  - [Log output v1.10](https://github.com/arkb2023/devops-kubernetes/tree/1.10/log_output)
  - [Ping pong v1.9](https://github.com/arkb2023/devops-kubernetes/tree/1.9/ping-pong)

**Application URLs**
- `Log output` app: `http://localhost:8081`
- `Ping pong` app: `http://localhost:8081/pingpong`

**Test Plan**
1. Validate Shared File Contents
    - Test initial value `0` for request count returnd by `Log output` app
    - Send `first` ping; `Ping pong` app returns 1 and `Log output` app also returns 1
    - Send `second` ping, `Ping pong` app returns 2 and `Log output` app also returns 2
2. Test Volume Persistence Across Pod Restarts
    - Restart both pods
    - Test `Log output` app still returns 2 (most recent value)
    - Send `third` ping'; `Ping pong` app returns 3 and `Log output` app also returns 3

***


### 1. **Directory and File Structure**
<pre>
├── volumes
│   ├── persistentvolume.yaml
│   └── persistentvolumeclaim.yaml
├── log_output
│   ├── README.md
│   ├── manifests
│   │   ├── deployment.yaml
│   │   ├── ingress.yaml
│   │   └── service.yaml
│   └── reader
│       ├── Dockerfile
│       └── reader.py
├── ping-pong
│   ├── Dockerfile
│   ├── README.md
│   ├── manifests
│   │   ├── deployment.yaml
│   │   ├── ingress.yaml
│   │   └── service.yaml
│   └── pingpong.py
</pre>

***




### 2. Prerequisites
- Docker, k3d, kubectl installed

### 3. Build and Push the Docker Image to DockerHub

```bash
docker build -t arkb2023/log-reader:1.11.2 ./log_output/reader/
docker build -t arkb2023/ping-pong:1.11.2 ./ping-pong/

docker push arkb2023/log-reader:1.11.2
docker push arkb2023/ping-pong:1.11.2
```
> Docker images are published at:  
https://hub.docker.com/repository/docker/arkb2023/ping-pong/tags/1.11.2  
https://hub.docker.com/repository/docker/arkb2023/log-reader/tags/1.11.2  

### 4. **Deploy to Kubernetes**

**Create cluster**

```bash
k3d cluster create --port 8081:80@loadbalancer --agents 2
```

**Setup Local PersistentVolume**  
To bind `PersistentVolume` to a local host path in a containerized node, create the backing storage directory inside the node container.

```bash
docker exec k3d-k3s-default-agent-0 mkdir -p /tmp/kube
```

**Apply the `Deployment` `Service` `Ingress` `PersistentVolume` and `PersistentVolumeClaim` Manifests**  

```bash
kubectl apply \
  -f ./log_output/manifests/deployment.yaml \
  -f ./log_output/manifests/ingress.yaml \
  -f ./log_output/manifests/service.yaml \
  -f ./ping-pong/manifests/deployment.yaml \
  -f ./ping-pong/manifests/service.yaml \
  -f ./ping-pong/manifests/ingress.yaml \
  -f volumes/persistentvolume.yaml \
  -f volumes/persistentvolumeclaim.yaml
```
*Output*
```text
deployment.apps/log-output-dep created
ingress.networking.k8s.io/dwk-log-output-ingress created
service/log-output-svc created
deployment.apps/ping-pong-dep created
service/ping-pong-svc created
ingress.networking.k8s.io/dwk-ping-pong-ingress created
persistentvolume/local-pv created
persistentvolumeclaim/local-pv-claim created
```

**Verify Both Pods Are Running**  
```bash
kubectl get pods
```
```text
NAME                             READY   STATUS    RESTARTS   AGE
log-output-dep-5d7749fbd-2v7qg   1/1     Running   0          94s
ping-pong-dep-76df77b665-rjjnn   1/1     Running   0          94s
```

**Verify `log-output-dep` and `ping-pong-dep` Deployments are using PersistentVolumeClaim**
```bash
kubectl describe deployments log-output-dep ping-pong-dep
```
*Under each depoyment, check the following in the output:*
- *Look for Volumes section with:*
  - *Type: `PersistentVolumeClaim`*
  - *ClaimName: `local-pv-claim`*
- *Under Containers, confirm the mount path shows `/usr/src/app/files`*

*Output*  
```text
Name:                   log-output-dep
Namespace:              default
CreationTimestamp:      Sun, 23 Nov 2025 10:12:47 +0530
Labels:                 <none>
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=log-output
Replicas:               1 desired | 1 updated | 1 total | 1 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=log-output
  Containers:
   log-reader:
    Image:        arkb2023/log-reader:1.11.2
    Port:         <none>
    Host Port:    <none>
    Environment:  <none>
    Mounts:
      /usr/src/app/files from shared-image (rw)
  Volumes:
   shared-image:
    Type:          PersistentVolumeClaim (a reference to a PersistentVolumeClaim in the same namespace)
    ClaimName:     local-pv-claim
    ReadOnly:      false
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   log-output-dep-5d7749fbd (1/1 replicas created)
Events:
  Type     Reason                 Age    From                   Message
  ----     ------                 ----   ----                   -------
  Warning  ReplicaSetCreateError  6m26s  deployment-controller  Failed to create new replica set "log-output-dep-5d7749fbd": Unauthorized
  Normal   ScalingReplicaSet      6m26s  deployment-controller  Scaled up replica set log-output-dep-5d7749fbd to 1

Name:                   ping-pong-dep
Namespace:              default
CreationTimestamp:      Sun, 23 Nov 2025 10:12:47 +0530
Labels:                 <none>
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app=ping-pong
Replicas:               1 desired | 1 updated | 1 total | 1 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  25% max unavailable, 25% max surge
Pod Template:
  Labels:  app=ping-pong
  Containers:
   ping-pong:
    Image:        arkb2023/ping-pong:1.11.2
    Port:         <none>
    Host Port:    <none>
    Environment:  <none>
    Mounts:
      /usr/src/app/files from shared-image (rw)
  Volumes:
   shared-image:
    Type:          PersistentVolumeClaim (a reference to a PersistentVolumeClaim in the same namespace)
    ClaimName:     local-pv-claim
    ReadOnly:      false
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   ping-pong-dep-76df77b665 (1/1 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  7m8s  deployment-controller  Scaled up replica set ping-pong-dep-76df77b665 to 1
```

**Verify PersistentVolumeClaim Configuration**  

```bash
kubectl describe pvc
```
> Check the following in the output:  
> - Status: `Bound`  
> - Volume: `local-pv`  
> - Used By: `log-output-dep-5d7749fbd-2v7qg`  
>            `ping-pong-dep-76df77b665-rjjnn`  

*Output*
```text
Name:          local-pv-claim
Namespace:     default
StorageClass:  manual
Status:        Bound
Volume:        local-pv
Labels:        <none>
Annotations:   pv.kubernetes.io/bind-completed: yes
               pv.kubernetes.io/bound-by-controller: yes
Finalizers:    [kubernetes.io/pvc-protection]
Capacity:      1Gi
Access Modes:  RWO
VolumeMode:    Filesystem
Used By:       log-output-dep-5d7749fbd-2v7qg
               ping-pong-dep-76df77b665-rjjnn
Events:        <none>
```

**Verify the PersistentVolume Configuration**
```bash
kubectl describe pv
```
> Check the following in the output:  
> - Status: `Bound`  
> - Claim: `default/local-pv-claim`  
> - Under `Soruce:`
>   - Type:  `LocalVolume`
>   - Path: `/tmp/kube`  

*Output* 
```text
Name:              local-pv
Labels:            <none>
Annotations:       pv.kubernetes.io/bound-by-controller: yes
Finalizers:        [kubernetes.io/pv-protection]
StorageClass:      manual
Status:            Bound
Claim:             default/local-pv-claim
Reclaim Policy:    Retain
Access Modes:      RWO
VolumeMode:        Filesystem
Capacity:          1Gi
Node Affinity:
  Required Terms:
    Term 0:        kubernetes.io/hostname in [k3d-k3s-default-agent-0]
Message:
Source:
    Type:  LocalVolume (a persistent volume backed by local storage on a node)
    Path:  /tmp/kube
Events:    <none>
```

**Inspect `ping-pong` container logs for application readiness**  
```bash
kubectl logs ping-pong-dep-76df77b665-rjjnn -c ping-pong
```  
*Output*  
```text
INFO:     Started server process [7]
INFO:     Waiting for application startup.
DEBUG:pingpong:Startup event: Log file path: /usr/src/app/files/pingpong-requests.txt
DEBUG:pingpong:Pingpong file does not exist. Starting from 0.
DEBUG:pingpong:Startup event: processing completed.
DEBUG:pingpong:Writing pingpong request count: 0
DEBUG:pingpong:Pingpong request count written: 0
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)
```

**Inspect `log reader` container logs for application readiness**  
```bash
kubectl logs log-output-dep-5d7749fbd-2v7qg -c log-reader
```  
*Output*  
```text
kubectl logs log-output-dep-5d7749fbd-2v7qg -c log-reader
INFO:     Started server process [7]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3000 (Press CTRL+C to quit)
```

### 5. Validate Shared File Contents   
- Access the `Log Output` application at: `http://localhost:8081`  
  ![Initial Log Output](./images/01-browser-log-output-app-response-pingpong-0.png)
  > Response shows the `initial timestamp` `random log string`, and `ping/pong count 0`—as expected.

- Ping: Send a request to the `Ping-pong` application endpoint at: `http://localhost:8081/pingpong`  
  ![Ping-pong Response 1](./images/02-browser-pingpong-app-response-1.png)  
  > The response confirms `pong 1`.

- Re-access `http://localhost:8081`
  ![Log Output After First Ping](./images/03-browser-log-output-app-response-pingpoing-1.png)
  > The updated response shows a new `timestamp` `random string` and `Ping / Pongs: 1`

- Ping: Send a second request to `http://localhost:8081/pingpong`
  ![Ping-pong Response 2](./images/04-browser-pingpong-app-response-2.png)
  > The response confirms `pong 2`.

- Access `http://localhost:8081` again.
  ![Log Output After Second Ping](./images/05-browser-log-output-app-response-pingpoing-2.png)
  > The updated response now confirms `Ping / Pongs: 2`.

This confirms that both applications read and write the shared count, proving successful persistent volume integration and data sharing.

### 6. Test Volume Persistence Across Pod Restarts
**Restart Both Pods**  
```bash
kubectl rollout restart deployment ping-pong-dep log-output-dep
```
*Output*
```text
deployment.apps/ping-pong-dep restarted
deployment.apps/log-output-dep restarted
```

**Wait Until Fresh Pods Reach Running State**
```bash
kubectl get pods
```
*Output*
```text
NAME                              READY   STATUS        RESTARTS   AGE
log-output-dep-5d7749fbd-2v7qg    1/1     Terminating   0          28m
log-output-dep-6c6b8dd87f-xqpnh   1/1     Running       0          11s
ping-pong-dep-75cc89c64d-r9bf8    1/1     Running       0          11s
ping-pong-dep-76df77b665-rjjnn    1/1     Terminating   0          28m
```

```bash
kubectl get pods
```
*Output*
```text
NAME                              READY   STATUS    RESTARTS   AGE
log-output-dep-6c6b8dd87f-xqpnh   1/1     Running   0          38s
ping-pong-dep-75cc89c64d-r9bf8    1/1     Running   0          38s
```

**Verify Persistence Post-Restart**  
- Access the `Log Output` application at `http://localhost:8081`
  ![Browser log-output application endpoint post restart](./images/06-browser-log-output-app-response-pingpoing-2-post-pod-restart.png)
  > The response shows the updated `timestamp` and `log string` with the `pre-restart ping/pong count of 2` confirming data persisted across pod restarts.

- Ping: Send a third request to `http://localhost:8081/pingpong`
  ![Browser ping-pong application endpoint ](./images/07-browser-pingpong-app-response-3.png)
  > The response returns `pong 3` as expected.

- Access `http://localhost:8081` again.
  ![Browser log-output application endpoint](./images/08-browser-log-output-app-response-pingpoing-3-post-pod-restart.png)
  > The updated `timestamp` `log string` and `Ping / Pongs count of 3` confirm smooth operation and reliable data persistence after an additional request and pod restart.

**Summary**   
These steps confirm that the persistent volume successfully retains data across multiple pod restarts and that both applications continue to read and write shared state consistently.

### 6. **Cleanup**

**Delete the `Deployment` `Service` `Ingress`  `PersistentVolume` and `PersistentVolumeClaim` Manifests** 
```bash
kubectl delete \
  -f ./log_output/manifests/deployment.yaml \
  -f ./log_output/manifests/ingress.yaml \
  -f ./log_output/manifests/service.yaml \
  -f ./ping-pong/manifests/deployment.yaml \
  -f ./ping-pong/manifests/service.yaml \
  -f ./ping-pong/manifests/ingress.yaml \
  -f volumes/persistentvolume.yaml \
  -f volumes/persistentvolumeclaim.yaml
```
*Output*
```text
deployment.apps "log-output-dep" deleted from default namespace
ingress.networking.k8s.io "dwk-log-output-ingress" deleted from default namespace
service "log-output-svc" deleted from default namespace
deployment.apps "ping-pong-dep" deleted from default namespace
service "ping-pong-svc" deleted from default namespace
ingress.networking.k8s.io "dwk-ping-pong-ingress" deleted from default namespace
persistentvolume "local-pv" deleted
persistentvolumeclaim "local-pv-claim" deleted from default namespace
```

**Stop the k3d Cluster**  
```bash
k3d cluster delete k3s-default
```
*Output*
```text
INFO[0000] Deleting cluster 'k3s-default'
INFO[0003] Deleting cluster network 'k3d-k3s-default'
INFO[0003] Deleting 1 attached volumes...
INFO[0003] Removing cluster details from default kubeconfig...
INFO[0003] Removing standalone kubeconfig file (if there is one)...
INFO[0003] Successfully deleted cluster k3s-default!
```

---

### Addendum: 
**Direct Shared Volume Validation**  
As an additional method to validate the shared persistent volume configuration, we can directly inspect the underlying and container-mounted file used for persistence. This is done by accessing the file from the node container as well as from inside each relevant pod. Consistent output across all locations confirms correct volume sharing and persistence.

```bash
# Check the physical file on the node
docker exec k3d-k3s-default-agent-0 cat /tmp/kube/pingpong-requests.txt

# Check from within the ping-pong container
kubectl exec -it ping-pong-dep-76df77b665-rjjnn -c ping-pong -- cat /usr/src/app/files/pingpong-requests.txt

# Check from within the log-output reader container
kubectl exec -it log-output-dep-5d7749fbd-2v7qg -c log-reader -- cat /usr/src/app/files/pingpong-requests.txt
```

