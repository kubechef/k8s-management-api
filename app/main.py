from fastapi import FastAPI, Query, Path, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.helpers import kube_helper
from app import auth, models, database
from .auth import create_access_token, get_current_user
from sqlalchemy.orm import Session
from app.api import deployments 

app = FastAPI()


@app.on_event("startup")
def startup():
    database.Base.metadata.create_all(bind=database.engine)

@app.post("/register")
def register(username: str = Body(...), password: str = Body(...), db: Session = Depends(auth.get_db)):
    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = models.User(username=username, hashed_password=auth.hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"msg": "User registered"}

@app.post("/login")
def login(username: str = Body(...), password: str = Body(...), db: Session = Depends(auth.get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_access_token({"sub": user.username})
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

# === Deployments ===
app.include_router(deployments.router)

# ==== Deployments ====
# @app.get("/deployments")
# def api_list_deployments(namespace: str = Query("default"), user=Depends(get_current_user)):
#     return kube_helper.list_deployments(namespace)


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
