from kubernetes import client, watch
from app.schemas.node_info import NodeInfo, NodeCondition, CombinedNodeInfo, ResourceUsage
import asyncio
from app.configs.ws_connection_manager import ConnectionManager

node_manager = ConnectionManager()

def get_node_info() -> list[CombinedNodeInfo]:
    v1 = client.CoreV1Api()
    nodes = v1.list_node().items
    node_infos = {}

    for node in nodes:
        status = node.status
        info = status.node_info
        capacity = status.capacity
        labels = node.metadata.labels or {}
        # Ambil role dari label
        role = labels.get('kubernetes.io/role')
        if not role:
            for key in labels:
                if key.startswith("node-role.kubernetes.io/"):
                    role = key.split('/')[-1]
                    break
            else:
                role = "N/A"

        # Ambil status Ready
        is_ready = any(
            c.type == "Ready" and c.status == "True"
            for c in status.conditions or []
        )
        node_infos[node.metadata.name] = NodeInfo(
            name=node.metadata.name,
            os_image=info.os_image,
            kubelet_version=info.kubelet_version,
            container_runtime_version=info.container_runtime_version,
            cpu=capacity.get("cpu", "N/A"),
            memory=capacity.get("memory", "N/A"),
            pod_capacity=capacity.get("pods", "N/A"),
            conditions=[
                NodeCondition(type=c.type, status=c.status)
                for c in status.conditions or []
            ],
            ready=is_ready,
            role=role
        )

    # Ambil metrics usage (CPU & memory)
    try:
        metrics_api = client.CustomObjectsApi()
        metrics = metrics_api.list_cluster_custom_object(
            group="metrics.k8s.io", version="v1beta1", plural="nodes"
        )
    except Exception:
        metrics = {"items": []}

    usage_data = {}
    for item in metrics.get("items", []):
        usage_data[item["metadata"]["name"]] = {
            "cpu": item["usage"]["cpu"],
            "memory": item["usage"]["memory"]
        }

    # Hitung jumlah pod per node
    pod_counts = {}
    all_pods = v1.list_pod_for_all_namespaces().items
    for pod in all_pods:
        node_name = pod.spec.node_name
        if node_name:
            pod_counts[node_name] = pod_counts.get(node_name, 0) + 1

    # Gabungkan data
    combined_data = []
    for node_name, node_info in node_infos.items():
        cpu_usage = usage_data.get(node_name, {}).get("cpu", "0")
        memory_usage = usage_data.get(node_name, {}).get("memory", "0")
        pod_usage = pod_counts.get(node_name, 0)

        resource_usage = ResourceUsage(
            node_name=node_name,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            pod_usage=str(pod_usage),
        )

        combined_data.append(CombinedNodeInfo(
            node_info=node_info,
            resource_usage=resource_usage
        ))

    return combined_data
