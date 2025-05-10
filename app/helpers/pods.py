from kubernetes import client, watch
from kubernetes.client import CoreV1Api, AppsV1Api, BatchV1Api
from fastapi import HTTPException
from app.schemas.pods import PodCreateRequest, PodListResponse, PodInfo, ContainerSpec

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


@handle_k8s_exception
def list_pods(namespace: str):
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace)

    return {
        "namespace": namespace,
        "pods": [
            {
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "node_name": pod.spec.node_name,
                "start_time": pod.status.start_time,
                "host_ip": pod.status.host_ip,
                "pod_ip": pod.status.pod_ip,
                "containers": [c.name for c in pod.spec.containers],
            }
            for pod in pods.items
        ]
    }

@handle_k8s_exception
def get_pod(namespace: str, pod_name: str):
    v1 = client.CoreV1Api()
    pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)

    return {
        "name": pod.metadata.name,
        "status": pod.status.phase,
        "node_name": pod.spec.node_name,
        "start_time": pod.status.start_time,
        "host_ip": pod.status.host_ip,
        "pod_ip": pod.status.pod_ip,
        "containers": [c.name for c in pod.spec.containers],
    }

@handle_k8s_exception
def create_pod(namespace: str, payload: PodCreateRequest):
    v1 = client.CoreV1Api()

    containers = []
    for c in payload.containers:
        containers.append(
            client.V1Container(
                name=c.name,
                image=c.image,
                command=c.command,
                args=c.args,
                env=[client.V1EnvVar(name=env.name, value=env.value) for env in (c.env or [])],
                volume_mounts=[
                    client.V1VolumeMount(name=vm.name, mount_path=vm.mountPath) for vm in (c.volumeMounts or [])
                ]
            )
        )

    volumes = []
    for v in payload.volumes or []:
        if v.emptyDir is not None:
            volumes.append(client.V1Volume(name=v.name, empty_dir=client.V1EmptyDirVolumeSource()))
        elif v.configMap is not None:
            volumes.append(client.V1Volume(
                name=v.name,
                config_map=client.V1ConfigMapVolumeSource(name=v.configMap["name"])
            ))

    pod_manifest = client.V1Pod(
        metadata=client.V1ObjectMeta(name=payload.name),
        spec=client.V1PodSpec(
            containers=containers,
            volumes=volumes
        )
    )

    resp = v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)
    return {"message": f"Pod '{resp.metadata.name}' berhasil dibuat di namespace '{namespace}'."}

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

@handle_k8s_exception
def delete_pod(namespace: str, name: str):
    try:
        core_v1.delete_namespaced_pod(name=name, namespace=namespace)
        return {"message": f"Pod '{name}' di namespace '{namespace}' berhasil dihapus."}
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)