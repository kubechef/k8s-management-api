from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class EnvVar(BaseModel):
    name: str
    value: str

class VolumeMount(BaseModel):
    name: str
    mountPath: str

class VolumeConfigMap(BaseModel):
    name: str

class Volume(BaseModel):
    name: str
    emptyDir: Optional[dict] = None
    configMap: Optional[VolumeConfigMap] = None

class Resources(BaseModel):
    limits: Optional[Dict[str, str]] = None
    requests: Optional[Dict[str, str]] = None

class DeploymentCreateRequest(BaseModel):
    name: str
    image: str
    replicas: int = 1
    ports: Optional[List[int]] = []
    env: Optional[List[EnvVar]] = []
    command: Optional[List[str]] = []
    args: Optional[List[str]] = []
    volumeMounts: Optional[List[VolumeMount]] = []
    volumes: Optional[List[Volume]] = []
    labels: Dict[str, str]
    resources: Optional[Resources] = None


class SecretRef(BaseModel):
    name: str

class EnvFromSource(BaseModel):
    secretRef: SecretRef


class EmptyDirVolume(BaseModel):
    medium: Optional[str] = None
    sizeLimit: Optional[str] = None


class DeploymentUpdateRequest(BaseModel):
    replicas: Optional[int] = Field(default=1)
    image: Optional[str]
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    ports: Optional[List[int]] = None
    env: Optional[List[EnvVar]] = None
    envFrom: Optional[List[EnvFromSource]] = None
    resources: Optional[Resources] = None
    volumeMounts: Optional[List[VolumeMount]] = None
    volumes: Optional[List[Volume]] = None
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None

