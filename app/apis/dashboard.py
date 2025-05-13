from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from app.helpers.auth import get_current_user
from app.helpers.events import get_recent_events
from app.helpers.node_info import get_node_info
from app.helpers.cluster_summary import get_cluster_summary


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/cluster/info")
def cluster_info():
 return get_cluster_summary()


@router.get("/nodes/info")
def nodes_info():
    return get_node_info()