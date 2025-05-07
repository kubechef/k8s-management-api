from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from typing import List
from app.helpers import kube_helper
from app.helpers.kube_helper import patch_deployment
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
    namespace: str = Query("default", description="Nama namespace"),
    name: str = Path(..., description="Nama deployment"),
    update_data: DeploymentUpdate = Body(..., description="Data yang akan diupdate"),
    user=Depends(get_current_user),
):
    update_dict = update_data.dict(exclude_unset=True)
    return patch_deployment(name, namespace, update_dict)



@router.delete("/{name}")
def delete_deployment(name: str, namespace: str = Query("default"), user=Depends(get_current_user)):
    return kube_helper.delete_deployment(name, namespace)


