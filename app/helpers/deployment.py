# === kube_helper.py ===
from kubernetes import client, config, watch
from kubernetes.client import CoreV1Api, AppsV1Api, BatchV1Api
from fastapi import HTTPException
from datetime import datetime
from typing import Optional, List



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

@handle_k8s_exception
def create_deployment(deploy_data):
    # Gunakan label "app" sebagai fallback
    default_app_label = {"app": deploy_data.name}

    # Gunakan selector atau fallback
    selector_labels = deploy_data.selector or deploy_data.labels or default_app_label

    # Gunakan labels untuk pod template dan metadata, harus match dengan selector
    template_labels = deploy_data.labels or selector_labels or default_app_label

    # Ambil container port dari payload
    container_port = deploy_data.container_port

    # Definisikan kontainer
    container = client.V1Container(
        name=deploy_data.name,
        image=deploy_data.image,
        ports=[client.V1ContainerPort(container_port=container_port)]
    )

    # Template pod dengan label yang cocok dengan selector
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=template_labels),
        spec=client.V1PodSpec(containers=[container])
    )

    # Selector harus cocok dengan label pada template
    spec = client.V1DeploymentSpec(
        replicas=deploy_data.replicas,
        selector=client.V1LabelSelector(match_labels=selector_labels),
        template=template
    )

    # Metadata deployment
    metadata = client.V1ObjectMeta(
        name=deploy_data.name,
        labels=template_labels  # Optional, hanya untuk penandaan deployment
    )

    # Buat objek deployment
    deployment = client.V1Deployment(
        metadata=metadata,
        spec=spec
    )

    # Kirim ke API Kubernetes
    result = apps_v1.create_namespaced_deployment(namespace=deploy_data.namespace, body=deployment)

    return {
        "status": "Success",
        "message": f"Deployment '{result.metadata.name}' created.",
        "timestamp": datetime.now().isoformat(),
        "labels": result.metadata.labels,
        "selector": result.spec.selector.match_labels,
        "name": result.metadata.name,
        "namespace": result.metadata.namespace,
        "replicas": result.spec.replicas,
        "image": result.spec.template.spec.containers[0].image,
        "container_port": container_port,
        "uid": result.metadata.uid,
        "creation_timestamp": result.metadata.creation_timestamp.isoformat()
    }





@handle_k8s_exception
def remove_deployment_labels(name: str, namespace: str, labels_to_remove: List[str]):
    deployment = apps_v1.read_namespaced_deployment(name, namespace)
    
    patch_ops = []

    # Hapus label dari metadata.labels
    for label in labels_to_remove:
        if deployment.metadata.labels and label in deployment.metadata.labels:
            patch_ops.append({
                "op": "remove",
                "path": f"/metadata/labels/{label}"
            })

    # Hapus label dari template.metadata.labels
    for label in labels_to_remove:
        if deployment.spec.template.metadata.labels and label in deployment.spec.template.metadata.labels:
            patch_ops.append({
                "op": "remove",
                "path": f"/spec/template/metadata/labels/{label}"
            })

    if not patch_ops:
        return {"status": "No labels to remove"}

    results = apps_v1.patch_namespaced_deployment(
        name, namespace, patch_ops
    )

    return {
        "status": "Success",
        "message": f"Labels removed from deployment '{name}'.",
        "removed": labels_to_remove,
        "updated_labels": results.metadata.labels
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
def patch_deployment(name: str, namespace: str, update_data: dict, labels_to_remove: List[str] = None):
    deployment = apps_v1.read_namespaced_deployment(name, namespace)

    # Update existing labels
    metadata_labels = deployment.metadata.labels or {}
    template_labels = deployment.spec.template.metadata.labels or {}

    if update_data.get("labels"):
        metadata_labels.update(update_data["labels"])
        template_labels.update(update_data["labels"])

    # Hapus labels jika diminta
    if labels_to_remove:
        for key in labels_to_remove:
            metadata_labels.pop(key, None)
            template_labels.pop(key, None)

    # Buat patch payload dengan labels yang telah diubah
    patch_payload = {
        "spec": {
            "replicas": update_data.get("replicas", deployment.spec.replicas),
            "template": {
                "metadata": {
                    "labels": template_labels
                },
                "spec": {
                    "containers": [
                        {
                            "name": deployment.spec.template.spec.containers[0].name,
                            "image": update_data.get("image", deployment.spec.template.spec.containers[0].image)
                        }
                    ]
                }
            }
        },
        "metadata": {
            "labels": metadata_labels
        }
    }

    result = apps_v1.patch_namespaced_deployment(name, namespace, patch_payload)
    return {
        "status": "Success",
        "labels": result.metadata.labels,
        "template_labels": result.spec.template.metadata.labels,
        "name": result.metadata.name,
        "namespace": result.metadata.namespace,
        "replicas": result.spec.replicas,
        "image": result.spec.template.spec.containers[0].image
    }

