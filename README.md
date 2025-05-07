# Kubernetes Management API

An API for managing and observing a Kubernetes cluster. Built with FastAPI and the Kubernetes Python client, this app uses JWT authentication and runs with `incluster_config` to integrate directly from inside a Kubernetes pod.

---

## ✅ Feature Checklist

### 🔒 Authentication
- [x] Login using username and password
- [x] Generate JWT token for access
- [x] Authorization middleware based on token

### 📦 Pods
- [x] List all pods in a namespace
- [x] Get logs from a specific pod
- [x] Real-time log streaming from pods (works with client like `curl` and soon I will implement it in `Flutter`)

### 🧱 Other Resources
- [x] List namespaces
- [x] List deployments
- [x] List services
- [x] List configmaps
- [x] List secrets
- [x] List statefulsets
- [x] List jobs
- [x] List daemonsets
- [x] List persistent volumes (PV)
- [x] List persistent volume claims (PVC)

---

## 🚧 Features Not Yet Available
- [ ] Create new deployments
- [ ] Update deployment/service/configmap configurations
- [ ] Delete resources (deployments, pods, etc.)
- [ ] Restart specific pods or deployments
- [ ] RBAC mapping based on JWT (multi-user access & scoped permissions)
- [ ] Custom metrics & observability dashboard (future Flutter frontend)
- [ ] WebSocket endpoint for log streaming (for Flutter)
- [ ] Error reporting & observability (Sentry, Prometheus, etc.)

---

## 📌 Planned Features

1. **Deployment CRUD**  
   - Create, update, delete deployments (and related services)

2. **Multi-User RBAC (JWT Claims-Based)**  
   - Users limited to specific namespaces

3. **Restart Resources**  
   - Endpoint to trigger rolling restarts for pods/deployments

4. **Dynamic Resource Creation via YAML Templates**  
   - Upload YAML from Flutter, validate and apply to cluster

5. **Monitoring Integration**  
   - Expose endpoint for Prometheus metrics

6. **Event Watcher & WebSocket**  
   - Push pod status/log events to Flutter client

---

## 📦 Installation & Deployment

### Prerequisites
- Active Kubernetes cluster
- ServiceAccount with appropriate access (role: view/edit)
- Docker and `kubectl` installed

### 1. Build Docker Image

```bash
docker build -t yourusername/kubechef-api:latest .
docker push yourusername/kubechef-api:latest
```

### 2. Deploy to Kubernetes Cluster

```bash
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```
---
## 📘 API Endpoints

`<BASE_URL>` is the actual IP address or domain where your backend service is exposed—either via a LoadBalancer, Ingress, or NodePort. Alternatively, you can access it locally using `kubectl port-forward`

```bash
kubectl port-forward svc/your-api-services 8080:80
```
### 🔒 Authentication

`POST <BASE_URL>/login`

#### Default Login:
- **Username**: `admin`
- **Password**: `password123`

if you want to change the default password to your own, modify in the `app/auth.py` at line:

```bash
def authenticate_user(username: str, password: str):
    return username == "<your-own-user>" and password == "<your-own-password>"
```
Upon successful login, you will receive an authorization bearer token. Use it as a header in your requests:
```bash
Auhorization: Bearer <your_token>
```

### 📦 Pods
`GET <BASE_URL>/pods`
List all pods in namespace.

`GET <BASE_URL>/pods/{namespace}/{podname}/logs`
View log from a pod.

`GET <BASE_URL>/pods/{namespace}/{podname}/logs/stream`
Realtime streaming log pod.

### 🧱 Kubernetes Resources
`GET <BASE_URL>/namespaces`
List all namespaces.

`GET <BASE_URL>/deployments`
List deployments in namespace.

`GET <BASE_URL>/services`
List services.

`GET <BASE_URL>/configmaps`
List configmaps.

`GET <BASE_URL>/secrets`
List secrets.

`GET <BASE_URL>/statefulsets`
List statefulsets.

`GET <BASE_URL>/jobs`
List jobs.

`GET <BASE_URL>/daemonsets`
List daemonsets.

`GET <BASE_URL>/pvs`
List Persistent Volumes (PV).

`GET <BASE_URL>/pvcs`
List Persistent Volume Claims (PVC).


