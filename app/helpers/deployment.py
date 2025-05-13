from kubernetes import client
from app.schemas.deployment import DeploymentCreateRequest, DeploymentUpdateRequest
from fastapi import HTTPException

def handle_k8s_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except client.exceptions.ApiException as e:
            raise HTTPException(status_code=e.status, detail=e.reason)
    return wrapper

@handle_k8s_exception
def create_deployment(namespace: str, payload: DeploymentCreateRequest):
    apps_v1 = client.AppsV1Api()

    # Handle volume mounts
    volume_mounts = [
        client.V1VolumeMount(name=vm.name, mount_path=vm.mountPath)
        for vm in (payload.volumeMounts or [])
    ]

    # Handle resources
    resources = None
    if payload.resources:
        resources = client.V1ResourceRequirements(
            limits=payload.resources.limits,
            requests=payload.resources.requests
        )

    # Define container
    container = client.V1Container(
        name=payload.name,
        image=payload.image,
        ports=[client.V1ContainerPort(container_port=port) for port in payload.ports or []],
        env=[client.V1EnvVar(name=e.name, value=e.value) for e in (payload.env or [])],
        command=payload.command,
        args=payload.args,
        volume_mounts=volume_mounts,
        resources=resources
    )

    # Handle volumes
    volumes = []
    for v in (payload.volumes or []):
        if v.emptyDir is not None:
            volumes.append(client.V1Volume(name=v.name, empty_dir=client.V1EmptyDirVolumeSource()))
        elif v.configMap is not None:
            volumes.append(client.V1Volume(name=v.name, config_map=client.V1ConfigMapVolumeSource(name=v.configMap.name)))

    # Pod template
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=payload.labels),
        spec=client.V1PodSpec(containers=[container], volumes=volumes)
    )

    # Deployment spec
    spec = client.V1DeploymentSpec(
        replicas=payload.replicas,
        selector=client.V1LabelSelector(match_labels=payload.labels),
        template=template
    )

    # Deployment object
    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=payload.name),
        spec=spec
    )

    apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)

    return {"message": f"Deployment '{payload.name}' berhasil dibuat di namespace '{namespace}'."}

@handle_k8s_exception
def update_deployment(namespace: str, name: str, payload: DeploymentUpdateRequest):
    apps_v1 = client.AppsV1Api()

    # Ambil deployment yang sudah ada
    deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)

    # Update field yang diizinkan
    deployment.spec.replicas = payload.replicas

    container = deployment.spec.template.spec.containers[0]
    container.image = payload.image
    container.command = payload.command
    container.args = payload.args
    container.env = [
        client.V1EnvVar(name=env.name, value=env.value) for env in (payload.env or [])
    ]
    container.env_from = [
        client.V1EnvFromSource(secret_ref=client.V1SecretEnvSource(name=env.secretRef.name))
        for env in (payload.envFrom or [])
    ]
    container.ports = [client.V1ContainerPort(container_port=p) for p in (payload.ports or [])]
    container.resources = client.V1ResourceRequirements(**payload.resources.dict()) if payload.resources else None
    container.volume_mounts = [
        client.V1VolumeMount(name=vm.name, mount_path=vm.mountPath) for vm in (payload.volumeMounts or [])
    ]

    deployment.spec.template.metadata.labels = payload.labels or {}
    deployment.spec.template.metadata.annotations = payload.annotations or {}

    deployment.spec.template.spec.volumes = []
    for v in payload.volumes or []:
        if v.emptyDir is not None:
            deployment.spec.template.spec.volumes.append(
                client.V1Volume(name=v.name, empty_dir=client.V1EmptyDirVolumeSource())
            )
        elif v.configMap is not None:
            deployment.spec.template.spec.volumes.append(
                client.V1Volume(
                    name=v.name,
                    config_map=client.V1ConfigMapVolumeSource(name=v.configMap["name"])
                )
            )

    # Kirim perubahan
    resp = apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)

    return {"message": f"Deployment '{name}' berhasil diupdate di namespace '{namespace}'."}

@handle_k8s_exception
def list_deployments(namespace: str):
    apps_v1 = client.AppsV1Api()
    deployments = apps_v1.list_namespaced_deployment(namespace=namespace)

    result = []
    for dep in deployments.items:
        container = dep.spec.template.spec.containers[0] if dep.spec.template.spec.containers else None

        result.append({
            "name": dep.metadata.name,
            "replicas": dep.spec.replicas,
            "labels": dep.metadata.labels,
            "annotations": dep.metadata.annotations,
            "image": container.image if container else None,
            "command": container.command if container else None,
            "args": container.args if container else None,
            "env": [{"name": e.name, "value": e.value} for e in (container.env or [])] if container else [],
            "ports": [p.container_port for p in (container.ports or [])] if container else [],
            "volumeMounts": [{"name": vm.name, "mountPath": vm.mount_path} for vm in (container.volume_mounts or [])] if container else [],
            "resources": container.resources.to_dict() if container and container.resources else {},
            "volumes": [
                {
                    "name": v.name,
                    "type": "emptyDir" if v.empty_dir else "configMap" if v.config_map else "other",
                    "configMap": {"name": v.config_map.name} if v.config_map else None
                }
                for v in (dep.spec.template.spec.volumes or [])
            ] if dep.spec.template.spec.volumes else []
        })

    return {"deployments": result}

@handle_k8s_exception
def get_deployment_detail(namespace: str, name: str):
    apps_v1 = client.AppsV1Api()
    dep = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)

    container = dep.spec.template.spec.containers[0] if dep.spec.template.spec.containers else None

    return {
        "name": dep.metadata.name,
        "replicas": dep.spec.replicas,
        "labels": dep.metadata.labels,
        "annotations": dep.metadata.annotations,
        "image": container.image if container else None,
        "command": container.command if container else None,
        "args": container.args if container else None,
        "env": [{"name": e.name, "value": e.value} for e in (container.env or [])] if container else [],
        "ports": [p.container_port for p in (container.ports or [])] if container else [],
        "volumeMounts": [{"name": vm.name, "mountPath": vm.mount_path} for vm in (container.volume_mounts or [])] if container else [],
        "resources": container.resources.to_dict() if container and container.resources else {},
        "volumes": [
            {
                "name": v.name,
                "type": "emptyDir" if v.empty_dir else "configMap" if v.config_map else "other",
                "configMap": {"name": v.config_map.name} if v.config_map else None
            }
            for v in (dep.spec.template.spec.volumes or [])
        ] if dep.spec.template.spec.volumes else []
    }

@handle_k8s_exception
def delete_deployment(namespace: str, name: str):
    apps_v1 = client.AppsV1Api()

    # Menghapus deployment
    apps_v1.delete_namespaced_deployment(
        name=name,
        namespace=namespace,
        body=client.V1DeleteOptions(propagation_policy="Foreground")
    )

    return {"message": f"Deployment '{name}' berhasil dihapus dari namespace '{namespace}'."}
