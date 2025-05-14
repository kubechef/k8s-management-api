from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from kubernetes import client, watch
import asyncio
from app.configs.ws_connection_manager import ConnectionManager

router = APIRouter()
event_manager = ConnectionManager()

@router.websocket("/dashboard/stream/events")
async def ws_events(websocket: WebSocket):
    # Terima koneksi WebSocket
    await event_manager.connect(websocket)
    print("✅ WebSocket connected for events")
    
    core = client.CoreV1Api()
    w = watch.Watch()
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()  # Simpan loop utama

    def event_watcher_blocking():
        try:
            print("🔍 Starting event watcher in background thread")
            for event in w.stream(core.list_event_for_all_namespaces, timeout_seconds=0):
                obj = event["object"]
                data = {
                    "type": event["type"],
                    "reason": obj.reason,
                    "message": obj.message,
                    "namespace": obj.metadata.namespace,
                    "involvedObject": {
                        "kind": obj.involved_object.kind,
                        "name": obj.involved_object.name,
                    },
                    "timestamp": obj.last_timestamp.isoformat() if obj.last_timestamp else None
                }
                # Kirim data ke queue dari thread ke main loop tanpa warning
                asyncio.run_coroutine_threadsafe(queue.put(data), loop)
        except Exception as e:
            print(f"❌ Exception in watcher thread: {e}")
        finally:
            w.stop()

    # Jalankan thread watcher
    watcher_task = loop.run_in_executor(None, event_watcher_blocking)

    try:
        # ⏱ Kirim semua event yang ada saat pertama kali terhubung (initial events)
        events = core.list_event_for_all_namespaces()
        for obj in events.items:
            initial_data = {
                "type": "INITIAL",
                "reason": obj.reason,
                "message": obj.message,
                "namespace": obj.metadata.namespace,
                "involvedObject": {
                    "kind": obj.involved_object.kind,
                    "name": obj.involved_object.name,
                },
                "timestamp": obj.last_timestamp.isoformat() if obj.last_timestamp else None
            }
            await websocket.send_json(initial_data)

        # ⏳ Kirim event baru yang diterima setelah itu melalui WebSocket
        while True:
            data = await queue.get()
            await event_manager.broadcast(data)

    except WebSocketDisconnect:
        print("⚠️ Client disconnected")
        event_manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        print("🔚 Closing WebSocket stream")
        watcher_task.cancel()