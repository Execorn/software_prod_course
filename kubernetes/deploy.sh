set -e

DOCKER_IMAGE_NAME="${DOCKER_USERNAME:-your-dockerhub-username}/fibonacci-app:latest"
NAMESPACE="default"

echo "--- Deploying Fibonacci App ---"
echo "Using Docker Image: ${DOCKER_IMAGE_NAME}"
echo "Target Namespace: ${NAMESPACE}"

echo "[1/5] Applying ConfigMap..."
kubectl apply -f kubernetes/configmap.yaml -n ${NAMESPACE}

TEMP_DEPLOYMENT_FILE=$(mktemp)
echo "Generating temporary deployment file..."

sed "s|execorn/fibonacci-app:latest|${DOCKER_IMAGE_NAME}|g" kubernetes/deployment.yaml >${TEMP_DEPLOYMENT_FILE}

echo "[2/5] Applying Deployment (using image ${DOCKER_IMAGE_NAME})..."
kubectl apply -f ${TEMP_DEPLOYMENT_FILE} -n ${NAMESPACE}

rm ${TEMP_DEPLOYMENT_FILE}

echo "[3/5] Applying Service..."
kubectl apply -f kubernetes/service.yaml -n ${NAMESPACE}

echo "[4/5] Applying DaemonSet (Log Agent)..."

kubectl apply -f kubernetes/daemonset.yaml -n ${NAMESPACE}

echo "[5/5] Applying CronJob (Log Archiver)..."
kubectl apply -f kubernetes/cronjob.yaml -n ${NAMESPACE}

echo "Waiting for Deployment to be ready..."
kubectl rollout status deployment/fibonacci-deployment -n ${NAMESPACE} --timeout=2m

echo "Waiting for DaemonSet to be ready..."

EXPECTED_DAEMONSETS=$(kubectl get nodes --no-headers | wc -l)

kubectl wait --for=condition=ready pod -l app=log-agent -n ${NAMESPACE} --timeout=2m || echo "Warning: DaemonSet pods might not be fully ready yet."

echo "--- Deployment Complete ---"

SERVICE_NAME="fibonacci-service"
echo "Fibonacci App Deployed."
echo "To access the service locally (in another terminal):"
echo "kubectl port-forward service/${SERVICE_NAME} -n ${NAMESPACE} 9090:80"
echo ""
echo "Example usage:"
echo "  curl http://localhost:9090/"
echo "  curl http://localhost:9090/status"
echo "  curl http://localhost:9090/fibonacci/15"
echo "  curl -X POST -H \"Content-Type: application/json\" -d '{\"message\": \"Deployed via script!\"}' http://localhost:9090/log"
echo "  curl http://localhost:9090/logs (shows logs from one pod)"
echo ""
echo "To check log agent logs (replace <agent-pod-name>):"
echo "  kubectl logs <agent-pod-name> -n ${NAMESPACE}"
echo ""
echo "To check CronJob status:"
echo "  kubectl get cronjob fibonacci-log-archiver -n ${NAMESPACE}"
echo "  kubectl get jobs -l job-name=fibonacci-log-archiver-* -n ${NAMESPACE}"
echo "---"

exit 0
