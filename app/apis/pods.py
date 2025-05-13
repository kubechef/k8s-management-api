from fastapi import APIRouter
from app.helpers.pods import list_pods, get_pod, get_pod_logs, stream_logs, create_pod, delete_pod
from app.helpers.auth import get_current_user
from fastapi import Query, Path, Depends
from fastapi.responses import StreamingResponse
from app.schemas.pods import PodCreateRequest, PodListResponse, PodInfo, ContainerSpec, ExecCommandRequest
from typing import Dict, List, Optional

router = APIRouter(prefix="/pods")

# === Pods Operation ===
@router.get("/{namespace}", response_model=PodListResponse)
def get_pods(namespace: str):
    return list_pods(namespace)

@router.get("/{namespace}/{pod_name}", response_model=PodInfo)
def get_pod_detail(namespace: str, pod_name: str):
    return get_pod(namespace, pod_name)

@router.post("/{namespace}")
def post_create_pod(namespace: str, payload: PodCreateRequest):
    return create_pod(namespace, payload)
   
# === Pods Logs ===
@router.get("/{namespace}/{pod_name}/logs")
def api_get_logs(pod_name: str, namespace: str, user=Depends(get_current_user)):
    return get_pod_logs(pod_name, namespace)

@router.get("/{namespace}/{pod_name}/logs/stream")
def api_stream_pod_logs(pod_name: str, namespace: str, user=Depends(get_current_user)):
    return StreamingResponse(
        stream_logs(namespace, pod_name),
        media_type="text/plain"
    )

@router.delete("/{namespace}/{name}")
def api_delete_pod(namespace: str, name: str, user=Depends(get_current_user)):
    return delete_pod(namespace, name)

# == Labels ==
@router.patch("/{namespace}/{pod_name}/labels")
def patch_pod_labels(namespace: str, pod_name: str, labels: Dict[str, str], user=Depends(get_current_user)):
    return update_pod_labels(namespace, pod_name, labels)

@router.delete("/{namespace}/{pod_name}/labels/{label_key}")
def remove_pod_label(namespace: str, pod_name: str, label_key: str, user=Depends(get_current_user)):
    return delete_pod_label(namespace, pod_name, label_key)

# == Annotations ==
@router.patch("/{namespace}/{pod_name}/annotations")
def patch_pod_annotations(namespace: str, pod_name: str, annotations: Dict[str, str], user=Depends(get_current_user)):
    return update_pod_annotations(namespace, pod_name, annotations)

@router.delete("/{namespace}/{pod_name}/annotations/{annotation_key}")
def remove_pod_annotation(namespace: str, pod_name: str, annotation_key: str, user=Depends(get_current_user)):
    return delete_pod_annotation(namespace, pod_name, annotation_key)

@router.post("/{namespace}/{pod_name}/exec")
def exec_pod_command(namespace: str, pod_name: str, body: ExecCommandRequest):
    return exec_command_in_pod(namespace, pod_name, body.command, body.container)

@router.post("/{namespace}/{pod_name}/restart")
def restart_pod_endpoint(namespace: str, pod_name: str):
    return restart_pod(namespace, pod_name)
