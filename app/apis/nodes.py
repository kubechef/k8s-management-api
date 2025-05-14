# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# from kubernetes import client, watch
# import asyncio
# from app.configs.ws_connection_manager import ConnectionManager

# router = APIRouter()
# node_manager = ConnectionManager()

# @router.websocket("/dashboard/stream/nodes")
# async def ws_nodes(websocket: WebSocket):
#     await node_manager.connect(websocket)
#     print("✅ WebSocket connected for nodes")

#     core = client.CoreV1Api()
#     w = watch.Watch()
#     queue = asyncio.Queue()
#     loop = asyncio.get_event_loop()

#     def node_watcher_blocking():
#         try:
#             print("🔍 Starting node watcher in background thread")
#             nodes = core.list_node()
#             resource_version = nodes.metadata.resource_version

#             for event in w.stream(core.list_node, resource_version=resource_version, timeout_seconds=0):
#                 obj = event["object"]
#                 data = {
#                     "type": event["type"],
#                     "name": obj.metadata.name,
#                     "status": next(
#                         (c.status for c in obj.status.conditions if c.type == "Ready"), "Unknown"
#                     ),
#                     "capacity": obj.status.capacity,
#                     "allocatable": obj.status.allocatable,
#                     "kubelet_version": obj.status.node_info.kubelet_version,
#                     "os_image": obj.status.node_info.os_image,
#                     "architecture": obj.status.node_info.architecture,
#                 }
#                 asyncio.run_coroutine_threadsafe(queue.put(data), loop)

#         except Exception as e:
#             print(f"❌ Exception in node watcher thread: {e}")
#         finally:
#             w.stop()

#     # Start background watcher
#     watcher_task = loop.run_in_executor(None, node_watcher_blocking)

#     try:
#         # ⏱ Kirim semua node sebagai INITIAL saat pertama connect
#         nodes = core.list_node()
#         for obj in nodes.items:
#             initial_data = {
#                 "type": "INITIAL",
#                 "name": obj.metadata.name,
#                 "status": next(
#                     (c.status for c in obj.status.conditions if c.type == "Ready"), "Unknown"
#                 ),
#                 "capacity": obj.status.capacity,
#                 "allocatable": obj.status.allocatable,
#                 "kubelet_version": obj.status.node_info.kubelet_version,
#                 "os_image": obj.status.node_info.os_image,
#                 "architecture": obj.status.node_info.architecture,
#             }
#             await websocket.send_json(initial_data)

#         # ⏳ Stream perubahan node
#         while True:
#             data = await queue.get()
#             await node_manager.broadcast(data)

#     except WebSocketDisconnect:
#         print("⚠️ Node WebSocket client disconnected")
#         node_manager.disconnect(websocket)
#     except Exception as e:
#         print(f"❌ WebSocket node error: {e}")
#     finally:
#         print("🔚 Closing Node WebSocket stream")
#         watcher_task.cancel()
# from kubernetes import client, watch
# from fastapi import APIRouter, WebSocket, WebSocketDisconnect
# import asyncio
# from app.configs.ws_connection_manager import ConnectionManager

# router = APIRouter()
# node_manager = ConnectionManager()

# @router.websocket("/dashboard/stream/nodes")
# async def ws_nodes(websocket: WebSocket):
#     await node_manager.connect(websocket)
#     print("✅ WebSocket connected for nodes")

#     core = client.CoreV1Api()
#     metrics_api = client.CustomObjectsApi()
#     w = watch.Watch()
#     queue = asyncio.Queue()
#     loop = asyncio.get_event_loop()

#     def node_watcher_blocking():
#         try:
#             print("🔍 Starting node watcher in background thread")
#             nodes = core.list_node()
#             resource_version = nodes.metadata.resource_version

#             for event in w.stream(core.list_node, resource_version=resource_version, timeout_seconds=0):
#                 obj = event["object"]
#                 node_name = obj.metadata.name

#                 try:
#                     # Ambil metrics node ini
#                     metrics = metrics_api.get_cluster_custom_object(
#                         group="metrics.k8s.io",
#                         version="v1beta1",
#                         plural="nodes",
#                         name=node_name
#                     )
#                     usage = metrics.get("usage", {})
#                     cpu_usage = usage.get("cpu", "0")
#                     memory_usage = usage.get("memory", "0")
#                 except Exception as e:
#                     print(f"⚠️ Failed to fetch metrics for {node_name}: {e}")
#                     cpu_usage = "0"
#                     memory_usage = "0"

#                 # Hitung pod per node
#                 pod_count = 0
#                 all_pods = core.list_pod_for_all_namespaces().items
#                 for pod in all_pods:
#                     if pod.spec.node_name == node_name:
#                         pod_count += 1

#                 data = {
#                     "type": event["type"],
#                     "name": node_name,
#                     "status": next(
#                         (c.status for c in obj.status.conditions if c.type == "Ready"), "Unknown"
#                     ),
#                     "capacity": obj.status.capacity,
#                     "allocatable": obj.status.allocatable,
#                     "cpu_usage": cpu_usage,
#                     "memory_usage": memory_usage,
#                     "pod_usage": pod_count,
#                     "kubelet_version": obj.status.node_info.kubelet_version,
#                     "os_image": obj.status.node_info.os_image,
#                     "architecture": obj.status.node_info.architecture,
#                 }

#                 asyncio.run_coroutine_threadsafe(queue.put(data), loop)

#         except Exception as e:
#             print(f"❌ Exception in node watcher thread: {e}")
#         finally:
#             w.stop()

#     # Jalankan watcher node di thread background
#     watcher_task = loop.run_in_executor(None, node_watcher_blocking)

#     try:
#         # 💡 Ambil metrics semua node di awal
#         try:
#             metrics = metrics_api.list_cluster_custom_object(
#                 group="metrics.k8s.io",
#                 version="v1beta1",
#                 plural="nodes"
#             )
#             metrics_map = {
#                 item["metadata"]["name"]: item["usage"]
#                 for item in metrics.get("items", [])
#             }
#         except Exception as e:
#             print("❌ Failed to fetch metrics:", e)
#             metrics_map = {}

#         # Hitung pod per node
#         pod_counts = {}
#         all_pods = core.list_pod_for_all_namespaces().items
#         for pod in all_pods:
#             node_name = pod.spec.node_name
#             if node_name:
#                 pod_counts[node_name] = pod_counts.get(node_name, 0) + 1

#         # Kirim semua node info sebagai INITIAL
#         nodes = core.list_node()
#         for obj in nodes.items:
#             name = obj.metadata.name
#             usage = metrics_map.get(name, {})
#             cpu_usage = usage.get("cpu", "0")
#             memory_usage = usage.get("memory", "0")
#             pod_count = pod_counts.get(name, 0)

#             initial_data = {
#                 "type": "INITIAL",
#                 "name": name,
#                 "status": next(
#                     (c.status for c in obj.status.conditions if c.type == "Ready"), "Unknown"
#                 ),
#                 "capacity": obj.status.capacity,
#                 "allocatable": obj.status.allocatable,
#                 "cpu_usage": cpu_usage,
#                 "memory_usage": memory_usage,
#                 "pod_usage": pod_count,
#                 "kubelet_version": obj.status.node_info.kubelet_version,
#                 "os_image": obj.status.node_info.os_image,
#                 "architecture": obj.status.node_info.architecture,
#             }
#             await websocket.send_json(initial_data)

#         # 🔁 Kirim perubahan dari watcher
#         while True:
#             data = await queue.get()
#             await node_manager.broadcast(data)

#     except WebSocketDisconnect:
#         print("⚠️ Node WebSocket client disconnected")
#         node_manager.disconnect(websocket)
#     except Exception as e:
#         print(f"❌ WebSocket node error: {e}")
#     finally:
#         print("🔚 Closing Node WebSocket stream")
#         watcher_task.cancel()


# == Optimasi ===#

from kubernetes import client, watch
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from app.configs.ws_connection_manager import ConnectionManager

router = APIRouter()
node_manager = ConnectionManager()

@router.websocket("/dashboard/stream/nodes")
async def ws_nodes(websocket: WebSocket):
    await node_manager.connect(websocket)
    print("✅ WebSocket connected for nodes")

    core = client.CoreV1Api()
    metrics_api = client.CustomObjectsApi()
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def fetch_node_metrics(node_name):
        try:
            metrics = metrics_api.get_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes",
                name=node_name
            )
            usage = metrics.get("usage", {})
            return usage.get("cpu", "0"), usage.get("memory", "0")
        except:
            return "0", "0"

    def build_node_data(obj, node_name, event_type, pod_count):
        cpu_usage, memory_usage = fetch_node_metrics(node_name)
        return {
            "type": event_type,
            "name": node_name,
            "status": next((c.status for c in obj.status.conditions if c.type == "Ready"), "Unknown"),
            "capacity": obj.status.capacity,
            "allocatable": obj.status.allocatable,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "pod_usage": pod_count,
            "kubelet_version": obj.status.node_info.kubelet_version,
            "os_image": obj.status.node_info.os_image,
            "architecture": obj.status.node_info.architecture,
        }

    def node_watcher():
        w = watch.Watch()
        try:
            nodes = core.list_node()
            rv = nodes.metadata.resource_version
            for event in w.stream(core.list_node, resource_version=rv, timeout_seconds=0):
                obj = event["object"]
                node_name = obj.metadata.name
                pod_count = sum(
                    1 for pod in core.list_pod_for_all_namespaces().items if pod.spec.node_name == node_name
                )
                data = build_node_data(obj, node_name, event["type"], pod_count)
                asyncio.run_coroutine_threadsafe(queue.put(data), loop)
        except Exception as e:
            print(f"❌ Node watcher error: {e}")
        finally:
            w.stop()

    def pod_watcher():
        w = watch.Watch()
        try:
            for event in w.stream(core.list_pod_for_all_namespaces, timeout_seconds=0):
                pod = event["object"]
                node_name = pod.spec.node_name
                if not node_name:
                    continue
                try:
                    obj = core.read_node(name=node_name)
                    pod_count = sum(
                        1 for p in core.list_pod_for_all_namespaces().items if p.spec.node_name == node_name
                    )
                    data = build_node_data(obj, node_name, "POD_UPDATE", pod_count)
                    asyncio.run_coroutine_threadsafe(queue.put(data), loop)
                except Exception as e:
                    print(f"❌ Pod watcher failed: {e}")
        except Exception as e:
            print(f"❌ Pod watcher error: {e}")
        finally:
            w.stop()

    node_task = loop.run_in_executor(None, node_watcher)
    pod_task = loop.run_in_executor(None, pod_watcher)

    try:
        print("📦 Sending initial node data")
        all_pods = core.list_pod_for_all_namespaces().items
        nodes = core.list_node()
        for obj in nodes.items:
            node_name = obj.metadata.name
            pod_count = sum(1 for pod in all_pods if pod.spec.node_name == node_name)
            data = build_node_data(obj, node_name, "INITIAL", pod_count)
            await websocket.send_json(data)

        while True:
            data = await queue.get()
            await node_manager.broadcast(data)

    except WebSocketDisconnect:
        print("⚠️ Node WebSocket client disconnected")
        node_manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        print("🔚 Closing WebSocket stream")
        node_task.cancel()
        pod_task.cancel()

