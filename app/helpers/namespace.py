from kubernetes import client, watch
from fastapi import HTTPException
from typing import Optional, Dict, List
from datetime import datetime
from fastapi import WebSocket
from typing import Iterator
from app.schemas.namespace import (
    NamespaceBase,
    K8snamespace,
    ResourceQuotaSpec,
    LimitRangeSpec,
    RBACSpec,
    RoleRule,
    Subject
)

core_v1 = client.CoreV1Api()
rbac_v1 = client.RbacAuthorizationV1Api()

# === Exception handler ===
def handle_k8s_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except client.exceptions.ApiException as e:
            raise HTTPException(status_code=e.status, detail=e.reason)
    return wrapper

# === NAMESPACE ===

@handle_k8s_exception
# def stream_namespaces(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             namespaces = core_v1.list_namespace()
#             namespace_names = [ns.metadata.name for ns in namespaces.items]
#             await websocket.send_json(namespace_names)
#     except Exception as e:
#         await websocket.close()
def stream_namespaces() -> Iterator[K8snamespace]:
    v1 = client.CoreV1Api()
    w = watch.Watch()

    print("🔄 Watching namespaces continuously...")

    while True:
        try:
            for namespace in w.stream(v1.list_namespace, timeout_seconds=60):
                obj = namespace["object"]
                yield K8snamespace(
                    name=obj.metadata.name,
                    status=obj.status.phase,
                    age=obj.metadata.creation_timestamp.isoformat() if obj.metadata.creation_timestamp else None,
                    labels=obj.metadata.labels,
                )
        except Exception as e:
            print(f"⚠️ Error in namespace stream: {e}")
            time.sleep(1) # retry delay


@handle_k8s_exception
def get_namespace_details(name: str):
    ns = core_v1.read_namespace(name=name)
    return {
        "name": ns.metadata.name,
        "labels": ns.metadata.labels,
        "creation_timestamp": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None,
        "status": ns.status.phase
    }

@handle_k8s_exception
def create_namespace(data: NamespaceBase):
    metadata = client.V1ObjectMeta(name=data.name, labels=data.labels)
    namespace = client.V1Namespace(metadata=metadata)
    result = core_v1.create_namespace(body=namespace)
    return {"message": f"Namespace '{result.metadata.name}' created."}

@handle_k8s_exception
def delete_namespace(name: str):
    core_v1.delete_namespace(name=name)
    return {"message": f"Namespace '{name}' deleted."}

@handle_k8s_exception
def patch_namespace_labels(name: str, labels: Dict[str, str]):
    body = {"metadata": {"labels": labels}}
    result = core_v1.patch_namespace(name=name, body=body)
    return {"message": f"Labels updated for namespace '{result.metadata.name}'."}

@handle_k8s_exception
def delete_namespace_labels(name: str, keys: List[str]):
    ns = core_v1.read_namespace(name=name)
    current_labels = ns.metadata.labels or {}

    patch_labels = {}
    for key in keys:
        if key in current_labels:
            patch_labels[key] = None  # Ini penting untuk menghapus label

    if not patch_labels:
        return {"message": f"Tidak ada label yang cocok dihapus dari namespace '{name}'."}

    body = {"metadata": {"labels": patch_labels}}
    core_v1.patch_namespace(name=name, body=body)
    return {"message": f"Label {keys} dihapus dari namespace '{name}'."}


# === RESOURCE QUOTA ===
@handle_k8s_exception
def get_resource_quotas(namespace: str):
    quotas = core_v1.list_namespaced_resource_quota(namespace=namespace)
    if not quotas.items:
        return [{"message": f"Tidak ada ResourceQuota di namespace '{namespace}'."}]
    return [
        {
            "name": quota.metadata.name,
            "hard": quota.status.hard,
            "used": quota.status.used
        }
        for quota in quotas.items
    ]

@handle_k8s_exception
def set_resource_quota(namespace: str, quota_spec: ResourceQuotaSpec):
    metadata = client.V1ObjectMeta(name="default-quota")
    spec = client.V1ResourceQuotaSpec(hard=quota_spec.hard)
    quota = client.V1ResourceQuota(metadata=metadata, spec=spec)
    core_v1.create_namespaced_resource_quota(namespace=namespace, body=quota)
    return {"message": f"ResourceQuota set in namespace '{namespace}'."}

@handle_k8s_exception
def update_resource_quota(namespace: str, quota_spec: ResourceQuotaSpec):
    core_v1.replace_namespaced_resource_quota(
        name=quota_spec.name,
        namespace=namespace,
        body=client.V1ResourceQuota(
            metadata=client.V1ObjectMeta(name=quota_spec.name),
            spec=client.V1ResourceQuotaSpec(hard=quota_spec.hard)
        )
    )
    return {"message": f"ResourceQuota '{quota_spec.name}' updated in namespace '{namespace}'."}

@handle_k8s_exception
def delete_resource_quota(namespace: str, quota_name: str):
    core_v1.delete_namespaced_resource_quota(name=quota_name, namespace=namespace)
    return {"message": f"ResourceQuota '{quota_name}' deleted from namespace '{namespace}'."}

# === LIMIT RANGE ===
@handle_k8s_exception
def set_limit_range(namespace: str, limit_spec: LimitRangeSpec):
    metadata = client.V1ObjectMeta(name="default-limit")
    item = client.V1LimitRangeItem(
        type=limit_spec.type,
        max=limit_spec.max,
        default=limit_spec.default,
    )
    spec = client.V1LimitRangeSpec(limits=[item])
    limit_range = client.V1LimitRange(metadata=metadata, spec=spec)
    core_v1.create_namespaced_limit_range(namespace=namespace, body=limit_range)
    return {"message": f"LimitRange set in namespace '{namespace}'."}

# === RBAC ===
@handle_k8s_exception
def create_role_and_binding(namespace: str, rbac_spec: RBACSpec):
    # Create Role
    role = client.V1Role(
        metadata=client.V1ObjectMeta(name=rbac_spec.role_name),
        rules=rbac_spec.rules
    )
    rbac_v1.create_namespaced_role(namespace=namespace, body=role)

    # Create RoleBinding
    binding = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(name=f"{rbac_spec.role_name}-binding"),
        subjects=[{
            "kind": "ServiceAccount",
            "name": rbac_spec.subjects[0].name,  # Updated for consistency
            "namespace": namespace
        }],
        role_ref={
            "kind": "Role",
            "name": rbac_spec.role_name,
            "apiGroup": "rbac.authorization.k8s.io"
        }
    )
    rbac_v1.create_namespaced_role_binding(namespace=namespace, body=binding)
    return {"message": f"RBAC Role and Binding created in namespace '{namespace}'."}
