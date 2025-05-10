from kubernetes import client
from kubernetes.client.rest import ApiException
from fastapi import HTTPException
import logging
import yaml
import textwrap


async def create_config_map_from_text(namespace: str, name: str, content: str, filename: str):
    try:
        config_map = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(name=name, namespace=namespace),
            data={filename: content}
        )

        api_instance = client.CoreV1Api()
        api_instance.create_namespaced_config_map(namespace=namespace, body=config_map)

        logging.info(f"ConfigMap '{name}' created in namespace '{namespace}'")

        return {
            "name": name,
            "namespace": namespace,
            "data": {filename: content},
            "message": f"ConfigMap '{name}' created successfully."
        }

    except ApiException as e:
        logging.error(f"API error while creating ConfigMap: {e}")
        raise e
    except Exception as e:
        logging.error(f"Unexpected error while creating ConfigMap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create ConfigMap: {str(e)}")



# Fungsi pembungkus yang dipanggil dari endpoint
async def create_config_map(namespace: str, name: str, filename: str, file_data: str):
    return await create_config_map_from_text(namespace, name, file_data, filename)


async def list_config_maps(namespace: str):
    try:
        api_instance = client.CoreV1Api()
        configmaps = api_instance.list_namespaced_config_map(namespace=namespace)

        return [
            {
                "name": item.metadata.name,
                "namespace": item.metadata.namespace,
                "data": item.data or {},
            }
            for item in configmaps.items
        ]
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)


# Mendapatkan detail ConfigMap berdasarkan nama
async def get_config_map(namespace: str, name: str, as_yaml: bool = False):
    try:
        api_instance = client.CoreV1Api()
        configmap = api_instance.read_namespaced_config_map(name=name, namespace=namespace)

        result = {
            "name": configmap.metadata.name,
            "namespace": namespace,
            "data": {
                k: ''.join(line.strip() for line in v.split('\n'))
                for k, v in (configmap.data or {}).items()
            }
        }

        if as_yaml:
            return yaml.dump(result, sort_keys=False, default_flow_style=False)
        return result

    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)

# Update ConfigMap (replace existing data)
async def update_config_map(namespace: str, name: str, filename: str, new_content: str):
    try:
        api_instance = client.CoreV1Api()

        # Dapatkan ConfigMap lama (untuk verifikasi exist)
        existing = api_instance.read_namespaced_config_map(name=name, namespace=namespace)

        # Perbarui isinya (bisa ditimpa hanya 1 key, atau semua)
        if not existing.data:
            existing.data = {}

        existing.data[filename] = new_content

        # Kirim pembaruan
        updated = api_instance.patch_namespaced_config_map(name=name, namespace=namespace, body=existing)

        return {
            "name": updated.metadata.name,
            "namespace": namespace,
            "data": updated.data,
            "message": f"ConfigMap '{name}' updated successfully."
        }

    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)

# Delete ConfigMap
async def delete_config_map(namespace: str, name: str):
    try:
        api_instance = client.CoreV1Api()
        api_instance.delete_namespaced_config_map(name=name, namespace=namespace)

        return {"message": f"ConfigMap '{name}' deleted from namespace '{namespace}'."}

    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)
