## Exercise 3.11. The project, step 19

**Objective**: Set sensible resource requests/limits for project pods using `kubectl top pods` for measurement.

**Approach**: Benchmark Baseline resource consumption, Set resource requests and limits with reasonable headroom. Test setup stability

**Setup:** GKE e2-medium nodes (2 vCPU, 4GB RAM × 3 nodes)

**1. Baseline Measurement:** 
  - Deployed app **without explicit resources/limits**
  - Generated continuous load (60s): `curl http://<IP>/` + `curl http://<IP>/todos` 
  - Captured 3×60s CPU and Memory metrics: `kubectl -n project top pods > metrics-*.txt`  
      ```bash
      cat metrics-*.txt
      ```
      Output:
      ```text
      NAME                                CPU(cores)   MEMORY(bytes)
      postgresql-db-0                     1m           42Mi
      todo-app-dep-575b95b59d-69cmh       4m           45Mi
      todo-backend-dep-69b8f4b96f-4stwn   3m           56Mi
      devops-kubernetes [main]$ cat metrics-2.txt
      NAME                                CPU(cores)   MEMORY(bytes)
      postgresql-db-0                     1m           42Mi
      todo-app-dep-575b95b59d-69cmh       3m           45Mi
      todo-backend-dep-69b8f4b96f-4stwn   3m           56Mi
      devops-kubernetes [main]$ cat metrics-3.txt
      NAME                                CPU(cores)   MEMORY(bytes)
      postgresql-db-0                     1m           42Mi
      todo-app-dep-575b95b59d-69cmh       4m           45Mi
      todo-backend-dep-69b8f4b96f-4stwn   3m           56Mi
      ```
  - **Results**: Max resource usage found to be approx,  
      - Frontend: 4.0m CPU, 45Mi Mem
      - Backend:  3.0m CPU, 56Mi Mem
      - Postgres: 1.0m CPU, 42Mi Mem
  - **Conclusion**: >95% headroom w.r.t. vCPU and Memory

**2. Test by setting explicit resource limits**
  - Patched deployments/StatefulSet with reasonable/sensible higher resource values,
    - Todo App Frontend:
      - requests 10m/64Mi, limits 50m/128Mi
      - Patch file: [todo-app-resources-patch.yaml](../apps/the-project/patch/todo-app-resources-patch.yaml)
      - Patch Todo frontend application  
        ```bash
        kubectl -n project patch deployment todo-app-dep \
          --patch-file=apps/the-project/patch/todo-app-resources-patch.yaml \
          --type=strategic
        ```
        Output:  
        ```text
        deployment.apps/todo-app-dep patched
        ```
      - Verify patch  
        ```bash
        kubectl -n project describe pod todo-app-dep-77b88987dc-tspwb | grep   " todo-app-dep\|Limits\|Requests\|cpu:\|memory:"
        ```
        Output:  
        ```text
        Name:             todo-app-dep-77b88987dc-tspwb
            Limits:
              cpu:     50m
              memory:  128Mi
            Requests:
              cpu:     10m
              memory:  64Mi
        ```

    - Todo Backend App:  
      - requests 10m/64Mi, limits 100m/128Mi  
      - Patch file: [todo-backend-resources-patch.yaml](../apps/the-project/patch/todo-backend-resources-patch.yaml)
      - Patch Todo backend application  
        ```bash
        kubectl -n project patch deployment todo-backend-dep \
        --patch-file=apps/the-project/patch/todo-backend-resources-patch.yaml \
        --type=strategic
        ```
        Output:  
        ```text
        deployment.apps/todo-backend-dep patched
        ```
      - Verify patch  
        ```bash
        kubectl -n project describe pod todo-backend-dep-54b4bdcf48-grq8t | grep   " todo-backend-dep\|Limits\|Requests\|cpu:\|memory:"
        ```
        Output:  
        ```text
        Name:             todo-backend-dep-54b4bdcf48-grq8t
            Limits:
              cpu:     100m
              memory:  128Mi
            Requests:
              cpu:     10m
              memory:  64Mi
        ```    

    - Postgres: 
      - Requests 50m/128Mi, limits 250m/256Mi
      - Patch file: [postgresql-resources-patch.yaml](../apps/the-project/patch/postgresql-resources-patch.yaml)
      - Patch Postgresql resources      
          ```bash
          kubectl -n project patch statefulset postgresql-db \
          --patch-file=apps/the-project/patch/postgresql-resources-patch.yaml \
          --type=strategic
          ```
          Output:
          ```text
          statefulset.apps/postgresql-db patched
          ```
          - Verify patch  
          ```bash
          kubectl -n project describe statefulset postgresql-db | grep   " postgresql-db\|Limits\|Requests\|cpu:\|memory:"
          ```
          Output:  
          ```text
          Name:               postgresql-db
            postgresql-db:
              Limits:
                cpu:     250m
                memory:  256Mi
              Requests:
                cpu:     50m
                memory:  128Mi
          ```

  - Re-tested load: 
    - Frontend peaked 50m CPU (limit hit)
    - Memory usage: 47%/46%/12% of limits (all <50%)
  - Captured CPU and Memory metrics: `kubectl -n project top pods > metrics-*.txt`  
    ```bash
    cat metrics-1.txt
    ```
    Output:
    ```text
    NAME                                CPU(cores)   MEMORY(bytes)
    postgresql-db-0                     1m           30Mi
    todo-app-dep-77b88987dc-tspwb       4m           44Mi
    todo-backend-dep-54b4bdcf48-grq8t   3m           56Mi
    NAME                                CPU(cores)   MEMORY(bytes)
    postgresql-db-0                     1m           30Mi
    todo-app-dep-77b88987dc-tspwb       50m          60Mi
    todo-backend-dep-54b4bdcf48-grq8t   9m           59Mi
    ```
  - Verified Stable deployment: No OOMKilled, No scheduling fails

    ```bash
    kubectl -n project get pods
    ```
    Output:
    ```text
    NAME                                 READY   STATUS      RESTARTS   AGE
    postgresql-db-0                      1/1     Running     0          59s
    todo-app-dep-77b88987dc-tspwb        1/1     Running     0          36m
    todo-backend-dep-54b4bdcf48-grq8t    1/1     Running     0          66s
    wiki-todo-generator-29419980-5tfds   0/1     Completed   0          74m
    wiki-todo-generator-29420040-g7kzs   0/1     Completed   0          14m
    ```

**Summary**
| Component | Requests     | Limits       | Max Usage | Headroom |
|-----------|--------------|--------------|-----------|----------|
| Frontend  | 10m/64Mi     | 50m/128Mi    | 50m/60Mi  | 0%/53%   |
| Backend   | 10m/64Mi     | 100m/128Mi   | 9m/59Mi   | 91%/54%  |
| Postgres  | 50m/128Mi    | 250m/256Mi   | 1m/30Mi   | 99%/88%  |
