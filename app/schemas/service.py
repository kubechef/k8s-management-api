from pydantic import BaseModel
from typing import List, Optional, Dict

class ServicePort(BaseModel):
    port: int
    targetPort: Optional[int] = None
    protocol: Optional[str] = "TCP"

class ServiceCreateRequest(BaseModel):
    name: str
    type: Optional[str] = "ClusterIP"
    selector: Dict[str, str]
    ports: List[ServicePort]
    labels: Optional[Dict[str, str]] = {}

class ServiceUpdateRequest(BaseModel):
    ports: Optional[List[ServicePort]]
    selector: Optional[Dict[str, str]]
    labels: Optional[Dict[str, str]]
