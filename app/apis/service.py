from fastapi import APIRouter
from app.helpers.service import (
    create_service, get_service_detail, update_service,
    delete_service, list_services
)
from app.schemas.service import ServiceCreateRequest, ServiceUpdateRequest

router = APIRouter(prefix="/services", tags=["Services"])

@router.get("/{namespace}")
def get_services(namespace: str):
    return list_services(namespace)

@router.get("/{namespace}/{name}")
def get_service(namespace: str, name: str):
    return get_service_detail(namespace, name)

@router.post("/{namespace}")
def create_k8s_service(namespace: str, payload: ServiceCreateRequest):
    return create_service(namespace, payload)

@router.patch("/{namespace}/{name}")
def update_k8s_service(namespace: str, name: str, payload: ServiceUpdateRequest):
    return update_service(namespace, name, payload)

@router.delete("/{namespace}/{name}")
def delete_k8s_service(namespace: str, name: str):
    return delete_service(namespace, name)
