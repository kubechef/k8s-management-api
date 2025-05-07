# === kube_helper.py ===
from kubernetes import client, config, watch
from kubernetes.client import CoreV1Api, AppsV1Api, BatchV1Api
from fastapi import HTTPException
from datetime import datetime

try:
    config.load_incluster_config()
except config.ConfigException as e:
    raise RuntimeError("Failed to load in-cluster config: " + str(e))

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

def load_kube_config():
    try:
        config.load_incluster_config()  # Untuk menjalankan di dalam cluster Kubernetes
    except Exception:
        config.load_kube_config()

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


# === DEPLOYMENT OPERATIONS ===
@handle_k8s_exception
def list_deployments(namespace: str):
    deployments = apps_v1.list_namespaced_deployment(namespace)
    return [
        {
            "name": d.metadata.name,
            "replicas": d.status.replicas or 0,
            "available": d.status.available_replicas or 0,
            "updated": d.status.updated_replicas or 0,
            "unavailable": d.status.unavailable_replicas or 0,
            "labels": d.metadata.labels,
            "annotations": d.metadata.annotations,
            "creation_timestamp": d.metadata.creation_timestamp.isoformat() if d.metadata.creation_timestamp else None,
            "namespace": d.metadata.namespace,
            "uid": d.metadata.uid,
            "image": d.spec.template.spec.containers[0].image if d.spec.template.spec.containers else None  # Menambahkan image
        } for d in deployments.items
    ]

# Get a specific deployment
@handle_k8s_exception
def get_deployment(name: str, namespace: str):
    deployment = apps_v1.read_namespaced_deployment(name, namespace)
    return {
        "name": deployment.metadata.name,
        "replicas": deployment.status.replicas or 0,
        "available": deployment.status.available_replicas or 0,
        "updated": deployment.status.updated_replicas or 0,
        "unavailable": deployment.status.unavailable_replicas or 0,
        "labels": deployment.metadata.labels,
        "annotations": deployment.metadata.annotations,
        "creation_timestamp": deployment.metadata.creation_timestamp,
        "namespace": deployment.metadata.namespace,
        "uid": deployment.metadata.uid
    }

# Create a deployment
@handle_k8s_exception
def create_deployment(deploy_data):
    container = client.V1Container(
        name=deploy_data.name,
        image=deploy_data.image,
        ports=[client.V1ContainerPort(container_port=80)],
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=deploy_data.labels or {"app": deploy_data.name}),
        spec=client.V1PodSpec(containers=[container])
    )
    spec = client.V1DeploymentSpec(
        replicas=deploy_data.replicas,
        selector={"matchLabels": deploy_data.labels or {"app": deploy_data.name}},
        template=template,
    )
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=deploy_data.name),
        spec=spec,
    )
    result = apps_v1.create_namespaced_deployment(namespace=deploy_data.namespace, body=deployment)

    return {
        "status": "Success",
        "message": f"Deployment '{result.metadata.name}' created.",
        "timestamp": datetime.now().isoformat(),
        "labels": result.metadata.labels,
        "name": result.metadata.name,
        "namespace": result.metadata.namespace,
        "replicas": result.spec.replicas,
        "image": result.spec.template.spec.containers[0].image,
        "uid": result.metadata.uid,
        "creation_timestamp": result.metadata.creation_timestamp.isoformat()
    }


# Delete a deployment
@handle_k8s_exception
def delete_deployment(name: str, namespace: str):
    result = apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
    return {
        "status": result.status,
        "message": "Deployment deleted",
    }


@handle_k8s_exception
def patch_deployment(name: str, namespace: str, update_data: dict):
    print(f"Received payload: {update_data}")  # Debugging the incoming payload
    deployment = apps_v1.read_namespaced_deployment(name, namespace)

    # Handle the labels update
    if update_data.get("labels"):
        print(f"Labels to update: {update_data['labels']}")  # Debugging labels
        if deployment.metadata.labels is None:
            deployment.metadata.labels = {}

        if deployment.spec.selector.match_labels is None:
            deployment.spec.selector.match_labels = {}

        if deployment.spec.template.metadata.labels is None:
            deployment.spec.template.metadata.labels = {}

        deployment.metadata.labels.update(update_data["labels"])
        deployment.spec.template.metadata.labels.update(update_data["labels"])
        deployment.spec.selector.match_labels.update(update_data["labels"])

    # Handle image update
    if update_data.get("image"):
        deployment.spec.template.spec.containers[0].image = update_data["image"]

    # Handle replicas update
    if update_data.get("replicas") is not None:
        deployment.spec.replicas = update_data["replicas"]

    # Prepare patch payload in the correct format
    patch_payload = {
        "spec": {
            "replicas": deployment.spec.replicas,
            "template": {
                "metadata": {
                    "labels": deployment.spec.template.metadata.labels
                },
                "spec": {
                    "containers": [
                        {
                            "name": deployment.spec.template.spec.containers[0].name,
                            "image": deployment.spec.template.spec.containers[0].image
                        }
                    ]
                }
            }
        },
        "metadata": {
            "labels": deployment.metadata.labels
        }
    }

    print(f"Patch payload: {patch_payload}")  # Debugging the payload that will be sent to Kubernetes

    # Patch the deployment
    try:
        results = apps_v1.patch_namespaced_deployment(name, namespace, patch_payload)
        return {
            "status": "Success",
            "message": f"Deployment '{results.metadata.name}' updated.",
            "timestamp": datetime.now().isoformat(),
            "labels": results.metadata.labels,
            "name": results.metadata.name,
            "namespace": results.metadata.namespace,
            "replicas": results.spec.replicas,
            "image": results.spec.template.spec.containers[0].image,
            "uid": results.metadata.uid,
            "creation_timestamp": results.metadata.creation_timestamp.isoformat()
        }
    except client.exceptions.ApiException as e:
        print(f"Error during patch operation: {e}")
        raise HTTPException(status_code=e.status, detail=f"Error during patch: {e.reason}")


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
