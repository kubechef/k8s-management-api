from fastapi import APIRouter, Depends
from app.helpers.deployment import create_deployment, update_deployment, list_deployments, get_deployment_detail, delete_deployment
from app.schemas.deployment import DeploymentCreateRequest, DeploymentUpdateRequest
from app.helpers.auth import get_current_user

router = APIRouter(prefix="/deployments")

@router.post("/{namespace}/create")
def create_k8s_deployment(namespace: str, payload: DeploymentCreateRequest, user=Depends(get_current_user)):
    return create_deployment(namespace, payload)

@router.put("/{namespace}/{name}/update")
def update_k8s_deployment(namespace: str, name: str, payload: DeploymentUpdateRequest, user=Depends(get_current_user)):
    return update_deployment(namespace, name, payload)

@router.get("/{namespace}/list")
def get_k8s_deployments(namespace: str, user=Depends(get_current_user)):
    return list_deployments(namespace)

@router.get("/{namespace}/{name}/info")
def get_k8s_deployment_detail(namespace: str, name: str, user=Depends(get_current_user)):
    return get_deployment_detail(namespace, name)

@router.delete("/{namespace}/{name}/delete")
def delete_k8s_deployment(namespace: str, name: str, user=Depends(get_current_user)):
    return delete_deployment(namespace, name)