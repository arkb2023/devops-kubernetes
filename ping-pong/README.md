## [Exercise 4.7. Baby steps to GitOps](https://courses.mooc.fi/org/uh-cs/courses/devops-with-kubernetes/chapter-5/gitops)  

**Instructions:**  

Move the Log output application to use GitOps so that when you commit to the repository, the application is automatically updated. (ArgoCD + GitHub Actions).

---

**Key Changes from Base:**  

- [`.github/workflows/gitops-log-output.yaml`](../.github/workflows/gitops-log-output.yaml): Defines GitHub Actions workflow that builds and pushes new Docker images for the exercises applications and updates Kustomize image references automatically on relevant path changes.
- [`environments/exercises-local/kustomization.yaml`](../environments/exercises-local/kustomization.yaml):  Updated the Kustomize configuration for exercises so images are driven by placeholders that the workflow replaces with immutable SHA tags, instead of manually managed version tags.

- Base application:  
  - [Log output v4.1](https://github.com/arkb2023/devops-kubernetes/tree/4.1/log_output)
  - [Ping pong v4.4](https://github.com/arkb2023/devops-kubernetes/tree/4.4/ping-pong)

---

**Directory and File Structure**  
<pre>
.github/                                        # github workflows root folder
└── workflows
    └── gitops-log-output.yaml                  # GitOps workflow for exercises (log-output + ping-pong)

environments/                                   # Multi-env overlays (local/GKE)
├── exercises-gke                               # GKE environment specific overlays
│   ├── gateway.yaml                            # Gateway API
│   ├── kustomization.yaml                      # Top level kustomization entry point 
│   ├── log-output-route.yaml                   # log-output HTTPRoute
│   ├── namespace.yaml                          # Namespace
│   └── ping-pong-route.yaml                    # ping-pong HTTPRoute
├── exercises-local                             # Local k3d environment specific overlays
│   ├── kustomization.yaml                      # Top level kustomization entry point
│   ├── log-output-ingress.yaml                 # log-output ingress
│   ├── namespace.yaml                          # Namespace
│   └── ping-pong-ingress.yaml                  # Ping-pong ingress

apps/                                           # Shared base resources
├── ping-pong-log-output                        # Consolidated app manifests + kustomization
│   ├── kustomization.yaml                      # Base manifests for ping-pong + log-output
│   ├── log-output-configmap.yaml               # log-output ConfigMap
│   ├── log-output-deployment.yaml              # log-output Deployment
│   ├── log-output-service.yaml                 # log-output Service 
│   ├── ping-pong-deployment.yaml               # ping-pong Deployment 
│   ├── ping-pong-service.yaml                  # ping-pong Service
│   ├── postgresql-configmap.yaml               # PostgreSQL ConfigMap
│   ├── postgresql-service.yaml                 # PostgreSQL Service
│   └── postgresql-statefulset.yaml             # PostgreSQL StatefulSet 

# Ping Pong application
ping-pong/
├── Dockerfile
├── README.md
└── pingpong.py

# Log output application
log_output/
├── generator
│   ├── Dockerfile
│   └── generator.py
└── reader
    ├── Dockerfile
    └── reader.py
</pre>

  
***

**Base Setup**  
- Docker  
- k3d (K3s in Docker)  
- kubectl (Kubernetes CLI)
- Create Cluster 
  ```bash
  k3d cluster create dwk-local --agents 2 --port 8081:80@loadbalancer
  ```

---

### 1. ArgoCD setup

```bash
kubectl create namespace argocd || true
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl port-forward svc/argocd-server -n argocd 8080:80
```
- Get admin password:  
  ```bash
  kubectl get secret argocd-initial-admin-secret -n argocd \
    -o jsonpath="{.data.password}" | base64 -d
  ```
- Access ArgoCD web UI at: `http://localhost:8080/applications`.
- Create a new ArgoCD Application pointing to `https://github.com/arkb2023/devops-kubernetes`, path `environments/exercises-local`, target namespace `exercises`, and then enable automatic sync for the application.
  ![caption](./images/00-create-argo-application.png)
  
### 2. GitHub Actions workflow

- Add the GitOps workflow: [`.github/workflows/gitops-log-output.yaml`](../.github/workflows/gitops-log-output.yaml).
- Configure GitHub Actions repository secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` for pushing images to Docker Hub.
- The workflow builds and pushes new `log-output` and `ping-pong` images on relevant path changes, runs `kustomize edit set image` to update `environments/exercises-local/kustomization.yaml`, and commits the change back to the `main` branch.

### 3. End-to-end GitOps: push → Actions → Argo auto-sync

- Make a small change in the log-output reader and push it:
  ```bash
  echo "# GitOps test" >> log_output/README.md
  git add log_output/README.md
  git commit -m "4.7 GitOps test" && git push
  ```
- GitHub Actions workflow [`Run #58287641941`](https://github.com/arkb2023/devops-kubernetes/actions/runs/20295309026/job/58287641941) is triggered, builds and pushes SHA-tagged images, updates `kustomization.yaml`, and commits the new image references.
  

  ![caption](./images/13-github-gitops-workflow-run.png)
    
  ![caption](./images/10-github-kustomization-sha-image-update.png)

  ![caption](./images/14-github-gitops-workflow-run-EndBug-add-and-commit-v9-step.png)

- ArgoCD detects the Git change, automatically syncs the `exercises-local` application, and rolls out the new versions of log-output and ping-pong (via Argo Rollouts canary for ping-pong) until the app is Healthy and Synced.

  ![caption](./images/01-argocd-ui-app-exercises-local.png)

    
  ![caption](./images/11-argocd-exercises-local-resources.png)
    
    
  ![caption](./images/12-argocd-exercises-local-resources-details.png)

- **Validation**  
  - All exercises pods running with new versions  
    ```bash
    kubectl get pods -n exercises
    ```
    Output:  
    ```bash
    NAME                                  READY   STATUS    RESTARTS        AGE
    log-output-dep-7898949b78-pj2kb       2/2     Running   0               57m
    ping-pong-rollout-6545974c45-l7gd4    1/1     Running   0               57m
    postgresql-db-0                       1/1     Running   3 (6h37m ago)   4d23h
    postgresql-db-1                       1/1     Running   3 (6h37m ago)   4d23h
    ```

  - Ping-pong rollout Healthy
    ```bash
    kubectl get rollout ping-pong-rollout -n exercises
    ```
    Output:  
    ```bash
    NAME                DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
    ping-pong-rollout   1         1         1            1           4d23h
    ```
  
  - Log output deployment and Ping-pong rollout using the same GitOps-managed SHA
    ```bash
    kubectl -n exercises describe rollout ping-pong-rollout | egrep -e "^Name:|Image"
    ```
    Output:  
    ```text
    Name:   ping-pong-rollout
            Image:  arkb2023/ping-pong:91fcf556ef02a3c5a9b1903105dbf804b9224ca7
    ```
    ```bash
    kubectl -n exercises describe deployment log-output-dep | egrep -e "^Name:|Image"
    ```
    Output:  
    ```text
    Name:   log-output-dep
            Image:  arkb2023/log-reader:91fcf556ef02a3c5a9b1903105dbf804b9224ca7
    ```

---

**Cleanup**

```bash
# Delete resources
kubectl delete namespace exercises 

# Delete Cluster
k3d cluster delete dwk-local
```
