## [Exercise: 5.5. Platform comparison](https://courses.mooc.fi/org/uh-cs/courses/devops-with-kubernetes/chapter-6/beyond-kubernetes)
### Instructions

Choose one service provider such as Rancher and compare it to another such as OpenShift.
Decide arbitrarily which service provider is "better" and argue for it against the other service provider.
For the submission a bullet points are enough.

---
### **Platform Comparison: Rancher vs Red Hat OpenShift**

**Scenario:**  
A mid‑size DevOps/platform team seeking flexible, upstream Kubernetes management across clouds (AWS/GCP/Azure), on‑prem, and edge, with limited budget and minimal vendor lock‑in.

**Recommendation:**  
Rancher is better than OpenShift for this team because it delivers lightweight, multi‑cluster management on any CNCF‑compliant Kubernetes with lower costs and higher portability.

**Evaluation based on:**  
Pricing & lock‑in, installation/operations, platform model/portability, developer experience, security & ecosystem.

***

### **1. Pricing & Lock-in**
**Rancher (Advantage):**
- Open-core model with free self-hosted version
- Commercial support priced per 2 cores/4 vCPUs at lower base rates vs. OpenShift.
- 100% Open Source Software
- Upstream Kubernetes (CNCF-conformant RKE2)
- Low lock-in—runs on any Linux/K8s (EKS, GKE, on-prem).

**OpenShift (Disadvantage):**
- Commercial-only subscriptions (per 2 cores/4 vCPUs)
- Higher total cost with RHEL CoreOS + managed variants (ROSA/ARO).
- Tight RHEL integration
- "Harder to escape" to vanilla Kubernetes once committed.

### **2. Installation & Operations**
**Rancher (Advantage):**
- Helm install on any CNCF-compliant cluster (or single-node RKE)
- Up in minutes to hours on Ubuntu/CentOS/RHEL/SLES.
- Simple rolling upgrades with minimal app downtime.

**OpenShift (Disadvantage):**
- Heavy bundled stack (CoreOS + 30+ Operators)
- Install takes days with more prerequisites.
- Over-The-Air updates via Cluster Version Operator are automated but more complex due to platform-wide orchestration.

### **3. Platform Model & Portability**
**Rancher (Advantage):**
- Multi-cluster UI for RKE2/K3s/EKS/GKE/on-prem/edge
- Stays true to upstream Kubernetes semantics
- Remove Rancher: clusters stay standard K8s (portable manifests/skills).

**OpenShift (Disadvantage):**
- Opinionated additions (Routes, strong networking/security defaults)
- Distinct platform flavor despite K8s API compatibility.
- Vendor lock-in risk
- Harder to revert to plain upstream K8s.

### **4. Developer Experience (CI/CD, Builds, Registry)**
**Rancher (Advantage for flexibility):**
- Modular integration with external tools (Jenkins, GitHub Actions, Fleet GitOps)
- No built-in but avoids bloat.
- Clean UI support for external registries (ECR, Harbor, Quay) - keeps platform lean.

**OpenShift (Strong but overkill):**
- Native Tekton Pipelines, S2I builds, visual console, integrated registry - full PaaS out-of-box.
- OperatorHub + certified ecosystem wired end-to-end (powerful but ties you in).

### **5. Security & Ecosystem**
**Rancher (Advantage for modularity):**
- Central auth/RBAC across clusters + NeuVector (runtime protection, L7 firewall, scanning).
- Partner Charts/SUSE ecosystem certified for RKE2/K3s, assemble flexibly.

**OpenShift (Strong defaults):**
- Built-in depth: non-root containers, Pod Security Admission, Advanced Cluster Security, Quay/Clair scanning.
- Certified OperatorHub with joint vendor support—enterprise confidence but Red Hat-centric.

---

### **Disclaimer:** 
This is an arbitrary comparison for educational purposes based on publicly available information. Actual experience varies by use case, version, and configuration. Rancher and OpenShift are both excellent platforms—choose based on specific needs.

---

### **References:**  
https://www.openlogic.com/blog/openshift-vs-kubernetes  
https://actsupport.com/rancher-vs-openshift-choose-the-ideal-platform-for-your-enterprise/  
https://www.densify.com/openshift-tutorial/rancher-vs-openshift/  
https://blog.purestorage.com/purely-educational/rancher-vs-openshift/  
https://rifaterdemsahin.com/2024/11/10/rancher-vs-openshift-a-comprehensive-comparison/  
https://www.qovery.com/blog/rancher-vs-openshift  
https://komodor.com/learn/rancher-vs-openshift-similarities-differences-how-to-choose/  
https://kifarunix.com/how-to-upgrade-openshift-cluster-step-by-step/  
https://cloudnativenow.com/editorial-calendar/best-of-2024/  
https://learn.microsoft.com/en-us/azure/openshift/howto-upgrade  
https://docs.openshift.com/container-platform/4.10/installing/index.html  
https://www.mirantis.com/openshift-vs-rancher-vs-mirantis/  
https://www.portainer.io/blog/rancher-vs-openshift  
https://trilio.io/resources/rancher-vs-openshift/  
https://www.portainer.io/blog/rancher-vs-openshift  
https://www.perplexity.ai/

---

