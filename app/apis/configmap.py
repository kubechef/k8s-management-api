from fastapi import APIRouter, HTTPException, UploadFile, Form, File, Depends
from kubernetes.client.rest import ApiException
from fastapi.responses import PlainTextResponse
from app.helpers.auth import get_current_user
from typing import Optional
from app.helpers.configmap import (
    create_config_map, get_config_map, list_config_maps,
    update_config_map, delete_config_map
)
from app.schemas.configmap import ConfigMapResponse, ConfigMapListItem, ConfigMapSingleItem

router = APIRouter(prefix="/ns")

@router.post("/{namespace}/configmaps/create", response_model=ConfigMapResponse)
async def create_configmap(
    namespace: str,
    name: str = Form(...),
    filename: str = Form(...),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user=Depends(get_current_user)
):
    if not file and not content:
        raise HTTPException(status_code=400, detail="Either 'file' or 'content' must be provided.")

    # Pilih apakah akan menggunakan content atau file
    file_data = content if content else (await file.read()).decode("utf-8")

    try:
        # Panggil helper untuk membuat ConfigMap
        created = await create_config_map(namespace, name, filename, file_data)
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)

    return created


@router.get("/{namespace}/configmaps", response_model=list[ConfigMapListItem])
async def list_configmaps(namespace: str):
    return await list_config_maps(namespace)


@router.get("/{namespace}/configmaps/{name}")
async def get_configmap(namespace: str, name: str, format: str = "json", user=Depends(get_current_user)):
    as_yaml = format.lower() == "yaml"
    result = await get_config_map(namespace, name, as_yaml=as_yaml)

    if as_yaml:
        return PlainTextResponse(content=result, media_type="text/plain")
    return result


@router.put("/{namespace}/configmaps/{name}", response_model=ConfigMapResponse)
async def update_configmap(
    namespace: str,
    name: str,
    filename: str = Form(...),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    user=Depends(get_current_user)
):

    if not file and not content:
        raise HTTPException(status_code=400, detail="Either 'file' or 'content' must be provided.")

    file_data = content if content else (await file.read()).decode("utf-8")

    try:
        created = await update_config_map(namespace, name, filename, file_data)
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.body)

    return await update_config_map(namespace, name, filename, file_data)


@router.delete("/{namespace}/configmaps/{name}")
async def delete_configmap(namespace: str, name: str, user=Depends(get_current_user)):
    result = await delete_config_map(namespace, name)
    return result
