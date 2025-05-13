from app.configs.kube_loader import load_kube_config
load_kube_config()
from fastapi import FastAPI, Query, Path, Depends, HTTPException, Body
from app.apis import auth, deployments, namespace, configmap, pods, service, dashboard, events
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.helpers import kube_helper
from app.helpers.auth import get_current_user
from app.db import database
from kubernetes import client, config, watch

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ganti sesuai kebutuhan, misalnya ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # atau ["POST", "GET"] jika ingin lebih ketat
    allow_headers=["*"],
)

app.include_router(dashboard.router, tags=["Dashboard"])

app.include_router(events.router, tags=["Events"])    

# ==== Auth ====
app.include_router(auth.router, tags=["Auth"])

# === Namespaces ===
app.include_router(namespace.router, tags=["Namespaces"])

# === Deployments ===
app.include_router(deployments.router)

# === ConfigMaps ===
app.include_router(configmap.router, tags=["ConfigMap"])

app.include_router(pods.router, tags=["Pods"])

app.include_router(service.router)



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
