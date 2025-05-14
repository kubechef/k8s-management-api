from fastapi import APIRouter, HTTPException, Query, Path, Depends, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import contextlib
from app.helpers.auth import get_current_user
from kubernetes import watch, client
from app.helpers.namespace import (
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
    create_role_and_binding, 
    stream_namespaces
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
    NamespaceLabelKeys,
    K8snamespace

)
from app.configs.ws_connection_manager import ConnectionManager


router = APIRouter()
manager = ConnectionManager()

@router.websocket("/dashboard/stream/namespaces")
async def ws_namespaces(websocket: WebSocket):
    # Accept WebSocket connection
    await manager.connect(websocket)
    v1 = client.CoreV1Api()
    w = watch.Watch()
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()  # Simpan loop utama

    def watch_namespaces_blocking():
        try:
            print("🔍 Starting namespace watcher in background thread")
            namespaces = v1.list_namespace()
            resource_version = namespaces.metadata.resource_version

            for event in w.stream(v1.list_namespace, resource_version=resource_version, timeout_seconds=0):
                obj = event["object"]
                data = {
                    "type": event["type"],
                    "name": obj.metadata.name,
                    "status": obj.status.phase,
                    "age": obj.metadata.creation_timestamp.isoformat() if obj.metadata.creation_timestamp else None,
                    "labels": obj.metadata.labels,
                }
                # Kirim data ke queue dari thread ke main loop tanpa warning
                asyncio.run_coroutine_threadsafe(queue.put(data), loop)

        except Exception as e:
            print(f"❌ Exception in watcher thread: {e}")
        finally:
            w.stop()

    # Jalankan thread watcher
    watcher_task = loop.run_in_executor(None, watch_namespaces_blocking)

    try:
        # ⏱ Kirim semua namespace saat pertama connect
        namespaces = v1.list_namespace()
        for obj in namespaces.items:
            initial_data = {
                "type": "INITIAL",
                "name": obj.metadata.name,
                "status": obj.status.phase,
                "age": obj.metadata.creation_timestamp.isoformat() if obj.metadata.creation_timestamp else None,
                "labels": obj.metadata.labels,
            }
            await websocket.send_json(initial_data)

        # ⏳ Kemudian mulai kirim event stream dari queue ke semua client yang terkoneksi
        while True:
            data = await queue.get()
            await manager.broadcast(data)

    except WebSocketDisconnect:
        print("⚠️ Client disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        print("🔚 Closing WebSocket stream")
        watcher_task.cancel()


# @router.websocket("/dashboard/stream/namespaces")
# async def ws_namespaces(websocket: WebSocket):
#     # 👉 Di sini bisa kamu validasi JWT token
#     # decode_jwt_token(token)
    
#     await websocket.accept()
#     loop = asyncio.get_event_loop()
#     print("✅ WebSocket connection accepted for namespaces")

#     def generator():
#         return stream_namespaces()

#     try:
#         async for namespace in _async_generator_from_thread(generator, loop):
#             data = {
#                 "name": namespace.name,
#                 "status": namespace.status,
#                 "age": namespace.age,
#                 "labels": namespace.labels,
#             }
#             await websocket.send_json(data)

#     except WebSocketDisconnect:
#         print("⚠️ WebSocket client disconnected.")

#     except Exception as e:
#         print(f"❌ WebSocket error: {e}")
#         with contextlib.suppress(RuntimeError):
#             await websocket.close(code=1011)

#     finally:
#         print("🔚 WebSocket streaming finished or disconnected.")

# async def _async_generator_from_thread(generator_func, loop):
#     it = generator_func()
#     while True:
#         try:
#             value = await loop.run_in_executor(None, next, it)
#             yield value
#         except StopIteration:
#             break
#         except asyncio.TimeoutError:
#             continue
#         except Exception as e:
#             print(f"Generator thread error: {e}")
#             break

# @router.get("/", response_model=List[str])
# def get_namespaces(user=Depends(get_current_user)):  # Menambahkan autentikasi
#     return list_namespaces()

@router.get("/namespace/{name}", response_model=dict)
def get_namespace_by_name(name: str, user=Depends(get_current_user)):
    return get_namespace_details(name)

@router.post("/namespace", response_model=dict)
def post_namespace(payload: NamespaceCreate, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return create_namespace(payload)

@router.delete("/namespace/{name}", response_model=dict)
def delete_namespace_by_name(name: str = Path(...), user=Depends(get_current_user)):  # Menambahkan autentikasi
    return delete_namespace(name)

@router.post("/namespace/{name}/labels", response_model=dict)
def update_namespace_labels(name: str, payload: NamespaceLabelUpdate, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return patch_namespace_labels(name, payload.labels)

@router.delete("/namespace/{name}/labels", response_model=dict)
def remove_labels_from_namespace(name: str, payload: NamespaceLabelKeys, user=Depends(get_current_user)):
    return delete_namespace_labels(name, payload.keys)

@router.get("/namespace/{name}/quotas", response_model=List[dict])
def list_quotas(name: str, user=Depends(get_current_user)):
    return get_resource_quotas(name)

@router.post("/namespace/{name}/quotas", response_model=dict)
def apply_resource_quota_route(name: str, payload: ResourceQuotaSpec, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return set_resource_quota(name, payload)

@router.put("/namespace/{name}/quotas", response_model=dict)
def update_quota(name: str, payload: ResourceQuotaSpec, user=Depends(get_current_user)):
    return update_resource_quota(name, payload)

@router.delete("/namespace/{name}/quotas/{quota_name}", response_model=dict)
def delete_quota(name: str, quota_name: str, user=Depends(get_current_user)):
    return delete_resource_quota(name, quota_name)

@router.post("/namespace/{name}/limits", response_model=dict)
def apply_limit_range(name: str, payload: LimitRangeSpec, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return set_limit_range(name, payload)

@router.post("/namespace/{name}/rbac", response_model=dict)
def set_rbac(name: str, payload: RBACSpec, user=Depends(get_current_user)):  # Menambahkan autentikasi
    return create_role_and_binding(name, payload)
