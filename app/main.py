from fastapi import FastAPI, Query, Path, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from . import kube_helper
from .auth import create_access_token, get_current_user, authenticate_user

app = FastAPI()

# ==== Auth ====

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(req: LoginRequest):
    if not authenticate_user(req.username, req.password):
        raise HTTPException(status_code=401, detail="Username/password salah")
    token = create_access_token({"sub": req.username})
    return {"access_token": token, "token_type": "bearer"}

# ==== Pods ====

@app.get("/pods")
def api_list_pods(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_pods(namespace)

@app.get("/pods/{name}/logs")
def api_get_logs(name: str = Path(...), namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.get_pod_logs(name, namespace)

@app.get("/pods/{pod_name}/logs/stream")
def api_stream_pod_logs(pod_name: str, namespace: str = Query("default"), user=Depends(get_current_user)):
    return StreamingResponse(
        kube_helper.stream_logs(namespace, pod_name),
        media_type="text/plain"
    )

# ==== Namespaces ====

@app.get("/namespaces")
def api_list_namespaces(user=Depends(get_current_user)):
    return kube_helper.list_namespaces()

# ==== Deployments ====

@app.get("/deployments")
def api_list_deployments(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_deployments(namespace)

@app.get("/services")
def get_services(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_services(namespace)

@app.get("/configmaps")
def get_configmaps(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_configmaps(namespace)

@app.get("/secrets")
def get_secrets(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_secrets(namespace)

@app.get("/statefulsets")
def get_statefulsets(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_statefulsets(namespace)

@app.get("/jobs")
def get_jobs(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_jobs(namespace)

@app.get("/daemonsets")
def get_daemonsets(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_daemonsets(namespace)

@app.get("/pvs")
def get_pvs(user=Depends(get_current_user)):
    return kube_helper.list_persistent_volumes()

@app.get("/pvcs")
def get_pvcs(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_persistent_volume_claims(namespace)
