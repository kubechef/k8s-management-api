from fastapi import APIRouter
from app.helpers.pods import list_pods, get_pod, get_pod_logs, stream_logs, create_pod, delete_pod
from app.helpers.auth import get_current_user
from fastapi import Query, Path, Depends
from fastapi.responses import StreamingResponse
from app.schemas.pods import PodCreateRequest, PodListResponse, PodInfo, ContainerSpec

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
