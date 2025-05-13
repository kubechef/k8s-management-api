from pydantic import BaseModel
from typing import List, Optional

class NodeCondition(BaseModel):
    type: str
    status: str

class NodeInfo(BaseModel):
    name: str
    os_image: str
    kubelet_version: str
    container_runtime_version: str
    cpu: str
    memory: str
    pod_capacity: str
    conditions: List[NodeCondition]
    ready: bool
    role: str


class ResourceUsage(BaseModel):
    node_name: str
    cpu_usage: str
    memory_usage: str
    pod_usage: str

class CombinedNodeInfo(BaseModel):
    node_info: NodeInfo
    resource_usage: Optional[ResourceUsage]
