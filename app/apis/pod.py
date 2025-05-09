from fastapi import FastAPI, APIRouter, Query, Path, Depends
from fastapi.responses import StreamingResponse
from app.helpers.auth import get_current_user
from app.helpers.pod import (
    list_pods,
    get_pod_logs,
    stream_logs
)

router = APIRouter(prefix="/pods")
# ==== Pods ====
@router.get("")
def api_list_pods(namespace: str = Query("default"), user=Depends(get_current_user)):
    return list_pods(namespace)

@router.get("/{name}/logs")
def api_get_logs(name: str = Path(...), namespace: str = Query("default"), user=Depends(get_current_user)):
    return get_pod_logs(name, namespace)

@router.get("/{pod_name}/logs/stream")
def api_stream_pod_logs(pod_name: str, namespace: str = Query("default"), user=Depends(get_current_user)):
    return StreamingResponse(
        stream_logs(namespace, pod_name),
        media_type="text/plain"
    )