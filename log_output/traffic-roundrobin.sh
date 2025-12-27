#!/bin/bash
ITERATIONS=${1:-100}
echo "Round-robin: $ITERATIONS iterations"
#kubectl port-forward svc/log-gateway-istio 8080:80 -n exercises &
PF_PID=$!
#sleep 3
for i in $(seq 1 $ITERATIONS); do
  curl -s -o /dev/null http://localhost:8080/
  curl -s -o /dev/null http://localhost:8080/pings
  curl -s -o /dev/null http://localhost:8080/pingpong
done
kill $PF_PID 2>/dev/null
echo "COMPLETE!"
#EOF

#chmod +x traffic-roundrobin.sh
#./traffic-roundrobin.sh 100
