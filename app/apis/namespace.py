from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import List
from app.helpers.auth import get_current_user
from app.helpers.namespace import (
    list_namespaces,
    get_namespace_details,
    create_namespace,
    delete_namespace,
    patch_namespace_labels,
    set_resource_quota,
    get_resource_quotas,
    update_resource_quota,
    delete_resource_quota,
    delete_namespace_labels,
    set_limit_range,
    create_role_and_binding
)
from app.schemas.namespace import (
    NamespaceBase,
    NamespaceCreate,
    ResourceQuotaSpec,
    LimitItem,
    LimitRangeSpec,
    RoleRule,
    Subject,
    RBACSpec,
    NamespaceLabelUpdate,
    NamespaceLabelKeys

)


router = APIRouter(prefix="/ns")

@router.get("/", response_model=List[str])
def get_namespaces(user=Depends(get_current_user)):  # Menambahkan autentikasi
    return list_namespaces()

@router.get("/{name}", response_model=dict)
def get_namespace_by_name(name: str, user=Depends(get_current_user)):
    return get_namespace_details(name)

@router.post("/", response_model=dict)
def post_namespace(payload: NamespaceCreate, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return create_namespace(payload)

@router.delete("/{name}", response_model=dict)
def delete_namespace_by_name(name: str = Path(...), user=Depends(get_current_user)):  # Menambahkan autentikasi
    return delete_namespace(name)

@router.post("/{name}/labels", response_model=dict)
def update_namespace_labels(name: str, payload: NamespaceLabelUpdate, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return patch_namespace_labels(name, payload.labels)

@router.delete("/{name}/labels", response_model=dict)
def remove_labels_from_namespace(name: str, payload: NamespaceLabelKeys, user=Depends(get_current_user)):
    return delete_namespace_labels(name, payload.keys)

@router.get("/{name}/quotas", response_model=List[dict])
def list_quotas(name: str, user=Depends(get_current_user)):
    return get_resource_quotas(name)

@router.post("/{name}/quotas", response_model=dict)
def apply_resource_quota_route(name: str, payload: ResourceQuotaSpec, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return set_resource_quota(name, payload)

@router.put("/{name}/quotas", response_model=dict)
def update_quota(name: str, payload: ResourceQuotaSpec, user=Depends(get_current_user)):
    return update_resource_quota(name, payload)

@router.delete("/{name}/quotas/{quota_name}", response_model=dict)
def delete_quota(name: str, quota_name: str, user=Depends(get_current_user)):
    return delete_resource_quota(name, quota_name)

@router.post("/{name}/limits", response_model=dict)
def apply_limit_range(name: str, payload: LimitRangeSpec, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return set_limit_range(name, payload)

@router.post("/{name}/rbac", response_model=dict)
def set_rbac(name: str, payload: RBACSpec, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return create_role_and_binding(name, payload)
