from app.configs.kube_loader import load_kube_config
load_kube_config()

from fastapi import FastAPI, Query, Path, Depends, HTTPException, Body
from app.apis import auth, deployments, namespace, configmap, pods

app = FastAPI()

from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.helpers import kube_helper
from app.helpers.auth import get_current_user
from app.db import database
from kubernetes import client, config, watch




# ==== Auth ====
app.include_router(auth.router, tags=["Auth"])

# === Namespaces ===
app.include_router(namespace.router, tags=["Namespaces"])

# === Deployments ===
app.include_router(deployments.router)

# === ConfigMaps ===
app.include_router(configmap.router, tags=["ConfigMap"])

app.include_router(pods.router, tags=["Pods"])


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
