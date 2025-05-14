from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from app.helpers.auth import get_current_user
from app.helpers.node_info import get_node_info
from app.helpers.cluster_summary import get_cluster_summary
from app.configs.ws_connection_manager import ConnectionManager
import asyncio

node_manager = ConnectionManager()

router = APIRouter()

@router.get("/dashboard/cluster/info")
def cluster_info():
 return get_cluster_summary()


@router.get("/dashboard/nodes/info")
def nodes_info():
    return get_node_info()

# @router.websocket("/dashboard/stream/nodes")
# async def ws_nodes(websocket: WebSocket):
#     await node_manager.connect(websocket)
#     print("✅ WebSocket connected for nodes")

#     queue = asyncio.Queue()  # Queue untuk menyimpan data

#     # Mulai streaming data node
#     await stream_node_info(websocket, queue)

#     # Jika WebSocket terputus, batalkan task
#     print("⚠️ WebSocket client disconnected")
#     node_manager.disconnect(websocket)
