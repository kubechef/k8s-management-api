from kubernetes import client, watch
from kubernetes.client import CoreV1Api
from fastapi import HTTPException

core_v1 = CoreV1Api()

def handle_k8s_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except client.exceptions.ApiException as e:
            raise HTTPException(status_code=e.status, detail=e.reason)
    return wrapper


# === POD OPERATIONS ===
@handle_k8s_exception
def list_pods(namespace: str):
    pods = core_v1.list_namespaced_pod(namespace)
    return [
        {
            "name": pod.metadata.name,
            "status": pod.status.phase,
            "node": pod.spec.node_name,
            "container_statuses": [
                {
                    "name": cs.name,
                    "ready": cs.ready,
                    "restart_count": cs.restart_count
                } for cs in pod.status.container_statuses
            ] if pod.status.container_statuses else [],
            "labels": pod.metadata.labels,
            "annotations": pod.metadata.annotations,
            "creation_timestamp": pod.metadata.creation_timestamp,
        }
        for pod in pods.items]

@handle_k8s_exception
def get_pod_logs(pod_name: str, namespace: str):
    log = core_v1.read_namespaced_pod_log(pod_name, namespace)
    return {"pod": pod_name, "log": log.strip().split("\n")}

@handle_k8s_exception
def stream_logs(namespace: str, pod_name: str):
    w = watch.Watch()
    for line in w.stream(
        core_v1.read_namespaced_pod_log,
        name=pod_name,
        namespace=namespace,
        follow=True,
        tail_lines=50,
        timestamps=True,
    ):
        yield line + "\n"
