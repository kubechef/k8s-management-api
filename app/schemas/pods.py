from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime

class PodInfo(BaseModel):
    name: str
    status: str
    node_name: Optional[str]
    start_time: Optional[datetime]
    host_ip: Optional[str]
    pod_ip: Optional[str]
    containers: List[str]

class PodListResponse(BaseModel):
    namespace: str
    pods: List[PodInfo]


class EnvVar(BaseModel):
    name: str
    value: str

class VolumeMount(BaseModel):
    name: str
    mountPath: str

class ContainerSpec(BaseModel):
    name: str
    image: str
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    env: Optional[List[EnvVar]] = None
    volumeMounts: Optional[List[VolumeMount]] = None

class VolumeSpec(BaseModel):
    name: str
    emptyDir: Optional[dict] = {}
    configMap: Optional[dict] = None

class PodCreateRequest(BaseModel):
    name: str
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None
    containers: List[ContainerSpec]
    volumes: Optional[List[VolumeSpec]] = None

class ExecCommandRequest(BaseModel):
    command: List[str]
    container: Optional[str] = None

