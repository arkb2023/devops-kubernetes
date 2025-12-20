#!/bin/bash
set -euo pipefail

NAMESPACE="production"
PV_NAME="production-local-pv"

echo "🚀 Nuclear production Cleanup Starting..."

# 1. Delete namespace + stuck PV (CORRECT SYNTAX)
echo "💥 Deleting namespace '$NAMESPACE' + PV '$PV_NAME'..."
kubectl delete namespace/"$NAMESPACE" pv/"$PV_NAME" --force --grace-period=0 --ignore-not-found=true

# 2. Wait + verify clean
echo "⏳ Waiting for cleanup (10s)..."
sleep 10

# 3. Double-check no remnants
echo "🔍 Verifying clean state..."
if kubectl get namespace "$NAMESPACE" &>/dev/null; then
  echo "❌ Namespace still exists!"
  exit 1
fi

if kubectl get pv "$PV_NAME" &>/dev/null; then
  echo "❌ PV still exists!"
  exit 1
fi

echo "✅ CLEAN SLATE ACHIEVED!"
echo "🎉 Ready for redeploy: kustomize build apps/the-project/overlays/prod | kubectl apply -f -"
