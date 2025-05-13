from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.helpers.events import get_recent_events, stream_events_sync, stream_events_sync_continuous
from fastapi.responses import JSONResponse
import asyncio
import contextlib
from concurrent.futures import ThreadPoolExecutor

router = APIRouter()
executor = ThreadPoolExecutor()
@router.websocket("/dashboard/stream/events")
async def ws_events(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_event_loop()
    print("✅ WebSocket connection accepted")

    def generator():
        return stream_events_sync_continuous()

    try:
        async for event in _async_generator_from_thread(generator, loop):
            data = {
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "involved_object": event.involved_object,
                "source": event.source,
                "timestamp": event.timestamp.isoformat()
               
            }
           # print(f"🔄 Sending event to WebSocket: {data}")
            await websocket.send_json(data)

    except WebSocketDisconnect:
        print("⚠️ WebSocket client disconnected.")

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        with contextlib.suppress(RuntimeError):
            await websocket.close(code=1011)

    finally:
        print("🔚 WebSocket streaming finished or disconnected.")

async def _async_generator_from_thread(generator_func, loop):
    it = generator_func()  # hanya sekali di awal
    while True:
        try:
            value = await loop.run_in_executor(None, next, it)
            yield value
        except StopIteration:
            break
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"Generator thread error: {e}")
            break
