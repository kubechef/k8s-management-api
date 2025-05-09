# === kube_helper.py ===
from kubernetes import client, config, watch
from kubernetes.client import CoreV1Api, AppsV1Api, BatchV1Api
from fastapi import HTTPException
from datetime import datetime
from typing import Optional, List

# try:
#     config.load_incluster_config()
# except config.ConfigException as e:
#     raise RuntimeError("Failed to load in-cluster config: " + str(e))

core_v1 = CoreV1Api()
apps_v1 = AppsV1Api()
batch_v1 = BatchV1Api()

def handle_k8s_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except client.exceptions.ApiException as e:
            raise HTTPException(status_code=e.status, detail=e.reason)
    return wrapper

# def load_kube_config():
#     try:
#         config.load_incluster_config()  # Untuk menjalankan di dalam cluster Kubernetes
#     except Exception:
#         config.load_kube_config()

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

# === Other Resources ===
@handle_k8s_exception
def list_namespaces():
    namespaces = core_v1.list_namespace()
    return [ns.metadata.name for ns in namespaces.items]


# === SERVICES OPERATIONS ===
@handle_k8s_exception
def list_services(namespace: str):
    services = core_v1.list_namespaced_service(namespace)
    return [
        {
            "name": s.metadata.name,
            "type": s.spec.type,
            "cluster_ip": s.spec.cluster_ip,
            "ports": [
                {
                    "port": p.port,
                    "protocol": p.protocol,
                    "target_port": p.target_port
                } for p in s.spec.ports
            ],
            "selector": s.spec.selector,
            "labels": s.metadata.labels
        } for s in services.items
    ]

@handle_k8s_exception
def list_configmaps(namespace: str):
    cms = core_v1.list_namespaced_config_map(namespace)
    return [
        {
            "name": cm.metadata.name,
            "data": cm.data,
            "labels": cm.metadata.labels,
            "annotations": cm.metadata.annotations,
            "creation_timestamp": cm.metadata.creation_timestamp,
            "namespace": cm.metadata.namespace
        } for cm in cms.items
    ]

@handle_k8s_exception
def list_secrets(namespace: str):
    secrets = core_v1.list_namespaced_secret(namespace)
    return [
        {
            "name": s.metadata.name,
            "type": s.type,
            "labels": s.metadata.labels,
            "annotations": s.metadata.annotations,
            "creation_timestamp": s.metadata.creation_timestamp,
            "namespace": s.metadata.namespace
        } for s in secrets.items
    ]

@handle_k8s_exception
def list_statefulsets(namespace: str):
    ssets = apps_v1.list_namespaced_stateful_set(namespace)
    return [{"name": s.metadata.name, "replicas": s.status.replicas or 0} for s in ssets.items]

@handle_k8s_exception
def list_jobs(namespace: str):
    jobs = batch_v1.list_namespaced_job(namespace)
    return [{"name": j.metadata.name, "succeeded": j.status.succeeded or 0} for j in jobs.items]

@handle_k8s_exception
def list_daemonsets(namespace: str):
    ds = apps_v1.list_namespaced_daemon_set(namespace)
    return [{"name": d.metadata.name, "desired": d.status.desired_number_scheduled or 0} for d in ds.items]

@handle_k8s_exception
def list_persistent_volumes():
    pvs = core_v1.list_persistent_volume()
    return [{"name": pv.metadata.name, "capacity": pv.spec.capacity.get("storage", "N/A")} for pv in pvs.items]

@handle_k8s_exception
def list_persistent_volume_claims(namespace: str):
    pvcs = core_v1.list_namespaced_persistent_volume_claim(namespace)
    return [{"name": pvc.metadata.name, "status": pvc.status.phase, "volume": pvc.spec.volume_name} for pvc in pvcs.items]
