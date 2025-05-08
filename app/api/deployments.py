from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from typing import List, Optional
from app.helpers import kube_helper
from app.helpers.kube_helper import patch_deployment, remove_deployment_labels
from app.auth import get_current_user
from app.schemas.deployments import DeploymentCreate, DeploymentUpdate, DeploymentResponse

router = APIRouter(prefix="/deployments", tags=["Deployments"])

@router.get("", response_model=List[DeploymentResponse])
def list_deployments(namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.list_deployments(namespace)

@router.get("/{name}")
def get_deployment(name: str, namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.get_deployment(name, namespace)

@router.post("")
def create_deployment(deploy: DeploymentCreate, user=Depends(get_current_user)):
    return kube_helper.create_deployment(deploy)

@router.patch("/{name}")
async def update_deployment(
    name: str,
    namespace: str = Query("default"),
    update_data: dict = Body(...),
    labels_to_remove: Optional[List[str]] = Query(None),
    user=Depends(get_current_user),
):
    return patch_deployment(name, namespace, update_data, labels_to_remove)


@router.patch("/{name}/labels/remove")
async def remove_labels(
    name: str,
    namespace: str = Query("default"),
    labels_to_remove: List[str] = Body(..., embed=True),
    user=Depends(get_current_user),
):
    return remove_deployment_labels(name, namespace, labels_to_remove)

@router.delete("/{name}")
def delete_deployment(name: str, namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.delete_deployment(name, namespace)


