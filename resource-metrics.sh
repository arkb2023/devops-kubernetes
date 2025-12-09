#!/bin/bash
# resource-metrics.sh - Automated Kubernetes Resource Baseline Calculator

NAMESPACE="project"
PODS=("todo-app-dep" "todo-backend-dep" "postgresql-db-0")
SNAPSHOTS=3
INTERVAL=60

echo "Starting Kubernetes Resource Baseline Measurement"
echo "Namespace: $NAMESPACE | Pods: ${PODS[*]} | Snapshots: $SNAPSHOTS x ${INTERVAL}s"

# Clear old metrics
rm -f metrics-*.txt

# Step 1: Capture snapshots
for i in $(seq 1 $SNAPSHOTS); do
  echo "Snapshot $i/$SNAPSHOTS..."
  kubectl -n $NAMESPACE top pods > "metrics-$i.txt"
  sleep $INTERVAL
done

echo ""
echo "Calculating averages..."
echo "================================================================"

# Step 2: Calculate per-pod averages
for pod in "${PODS[@]}"; do
  # CPU average (column 2)
  cpu_avg=$(awk -v pod="$pod" '
    $1 ~ pod {sum+=$2; c++} 
    END {if(c>0) printf "%.1fm", sum/c; else print "N/A"}' metrics-*.txt)
  
  # Memory average (column 3)
  mem_avg=$(awk -v pod="$pod" '
    $1 ~ pod {sum+=$3; c++} 
    END {if(c>0) printf "%.0fMi", sum/c; else print "N/A"}' metrics-*.txt)
  
  echo "$pod → CPU: $cpu_avg | Memory: $mem_avg"
done

echo ""
echo "Conservative Resource Recommendations:"
echo "=========================================="
cat << 'EOF'
Frontend (todo-app-dep):
  requests: cpu: "10m", memory: "64Mi"
  limits:   cpu: "50m",  memory: "128Mi"

Backend (todo-backend-dep):
  requests: cpu: "10m", memory: "64Mi" 
  limits:   cpu: "100m", memory: "128Mi"

Postgres (postgresql-db-0):
  requests: cpu: "50m", memory: "128Mi"
  limits:   cpu: "250m", memory: "256Mi"
EOF

echo ""
echo "Metrics saved to: metrics-*.txt"
echo "Screenshot: kubectl -n project top pods (final snapshot)"
echo "Ready for Exercise 3.11 resource limits!"
