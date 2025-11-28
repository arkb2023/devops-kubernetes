#!/usr/bin/env bash
#   Use this script to test jobs manually

# Delete existing CronJob (disable hourly)
kubectl delete cronjob wiki-todo-generator -n project

# Create rapid-fire manual jobs for testing
for i in {1..10}; do
  kubectl create job --from=cronjob/wiki-todo-generator manual-test-$i -n project
  sleep 20
done

# Watch all logs
kubectl logs -f -n project -l job-name=manual-test-