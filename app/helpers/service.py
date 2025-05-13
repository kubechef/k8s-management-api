from kubernetes import client
from fastapi import HTTPException
from app.schemas.service import ServiceCreateRequest, ServiceUpdateRequest

def handle_k8s_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except client.exceptions.ApiException as e:
            raise HTTPException(status_code=e.status, detail=e.reason)
    return wrapper

@handle_k8s_exception
def create_service(namespace: str, payload: ServiceCreateRequest):
    core_v1 = client.CoreV1Api()

    ports = [client.V1ServicePort(port=p.port, target_port=p.targetPort, protocol=p.protocol) for p in payload.ports]

    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=payload.name, labels=payload.labels),
        spec=client.V1ServiceSpec(
            selector=payload.selector,
            ports=ports,
            type=payload.type
        )
    )

    core_v1.create_namespaced_service(namespace=namespace, body=service)
    return {"message": f"Service '{payload.name}' berhasil dibuat di namespace '{namespace}'."}

@handle_k8s_exception
def get_service_detail(namespace: str, name: str):
    core_v1 = client.CoreV1Api()
    svc = core_v1.read_namespaced_service(name=name, namespace=namespace)

    return {
        "name": svc.metadata.name,
        "type": svc.spec.type,
        "selector": svc.spec.selector,
        "labels": svc.metadata.labels,
        "ports": [
            {"port": p.port, "targetPort": p.target_port, "protocol": p.protocol}
            for p in svc.spec.ports or []
        ]
    }

@handle_k8s_exception
def update_service(namespace: str, name: str, payload: ServiceUpdateRequest):
    core_v1 = client.CoreV1Api()
    svc = core_v1.read_namespaced_service(name=name, namespace=namespace)

    if payload.ports:
        svc.spec.ports = [client.V1ServicePort(port=p.port, target_port=p.targetPort, protocol=p.protocol) for p in payload.ports]
    if payload.selector:
        svc.spec.selector = payload.selector
    if payload.labels:
        svc.metadata.labels = payload.labels

    core_v1.patch_namespaced_service(name=name, namespace=namespace, body=svc)
    return {"message": f"Service '{name}' berhasil diupdate di namespace '{namespace}'."}

@handle_k8s_exception
def delete_service(namespace: str, name: str):
    core_v1 = client.CoreV1Api()
    core_v1.delete_namespaced_service(name=name, namespace=namespace)
    return {"message": f"Service '{name}' berhasil dihapus dari namespace '{namespace}'."}

@handle_k8s_exception
def list_services(namespace: str):
    core_v1 = client.CoreV1Api()
    services = core_v1.list_namespaced_service(namespace=namespace)

    result = []
    for svc in services.items:
        result.append({
            "name": svc.metadata.name,
            "type": svc.spec.type,
            "selector": svc.spec.selector,
            "labels": svc.metadata.labels,
            "ports": [
                {"port": p.port, "targetPort": p.target_port, "protocol": p.protocol}
                for p in svc.spec.ports or []
            ]
        })

    return {"services": result}
