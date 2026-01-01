## [Exercise: 3.9. DBaaS vs DIY](https://courses.mooc.fi/org/uh-cs/courses/devops-with-kubernetes/chapter-4/gke-features#43e93b24-c10c-4063-8b71-7130322f871a)

### **Instructions**

Do a pros/cons comparison of the solutions in terms of meaningful differences. This includes at least the required work and costs to initialize as well as the maintenance. Backup methods and their ease of usage should be considered as well.

Write your answer in the README of the project.

---

### **Comparison:** DBaaS (Cloud SQL) vs DIY (PVC + Postgres)

#### **1. Initialize & Run**
**DIY PVC + Postgres:**
- Provisioned through user defined `kubectl apply statefulset.yaml`
- Persistent Disk auto-provisioned via `pd-standard` StorageClass
- Init time ~ 5 minutes 

**DBaaS Cloud SQL:**
- `gcloud sql instances create` + VPC peering/Cloud SQL Proxy setup
- Init time ~ 10-15 minutes, 

#### **2. Costs**
**DIY PVC + Postgres:**
- Raw GCE PD + engineer time (~$0.17/GB + automation effort)
- 10GB PD-SSD = $1.70/month + GKE nodes = ~$2-5/month dev
- Ops responsibility: upgrades, monitoring, IOPS tuning

**DBaaS (Cloud SQL):**
- Managed premium: $94/month (db-f1-micro) + storage = ~$100/month dev
- Production: $500+/month (handles patching, HA)

#### **3. Maintenance**
**DIY PVC + Postgres:**
- Manual: StatefulSet scaling, Prometheus/Grafana monitoring, image upgrades

**DBaaS (Cloud SQL):**
- **Automatic**: Scaling, patching, Cloud Monitoring
- `--availability-type=REGIONAL` for multi-zone HA

#### **4. Backup**
**DIY PVC + Postgres:**
- Manual `pg_dump` cron + GCS/Velero, WAL-G/Barman for PITR
- Engineer time to script/test everything

**DBaaS (Cloud SQL):**
- Automated daily + PITR (7 days), 1-click GCS export
- Disk snapshots (crash-consistent, no perf impact)

#### **5. Ease of Use**
**DIY PVC + Postgres:**
- Full freedom: Any extension (GIS/AI), custom `postgresql.conf`, Local SSDs
- Superuser access

**DBaaS (Cloud SQL):**
- Simple but restricted: No OS access, limited extensions, no superuser

### **6. Suitability****

**DIY (PVC + Postgres):**
- Cost-sensitive/learning teams, early-stage apps

**DBaaS (Cloud SQL):**
- Production velocity where ops cost > infra cost

### 7. Scalability
**DIY (PVC + Postgres):**
- Manual or Operator-driven (StatefulSet replicas)

**DBaaS (Cloud SQL):**
- Vertical easy + read replicas (horizontal)

### **8. Vendor Lock-in**
**DIY (PVC + Postgres):**
- Low — standard Postgres + PVCs (portable)

**DBaaS (Cloud SQL):**
- High — GCP-specific APIs/IAM

---

**Disclaimer:**  
Educational comparison based on public docs. Costs approximate. Test for your workload.

---

**References:**  
- [GKE Database Options](https://cloud.google.com/kubernetes-engine/docs/concepts/database-options)
- [Cloud SQL Pricing](https://cloud.google.com/sql/pricing)
- [GKE Persistent Disk Pricing](https://cloud.google.com/compute/disks-image-pricing)
- [GKE Storage Classes](https://cloud.google.com/kubernetes-engine/docs/concepts/persistent-volumes)
- [Pricing Calculator](https://cloud.google.com/products/calculator)

