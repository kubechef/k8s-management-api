from pydantic import BaseModel
from typing import Optional, Dict

# Model untuk create deployment
class DeploymentCreate(BaseModel):
    name: str
    namespace: str
    image: str
    replicas: int
    labels: Optional[Dict[str, str]] = None 

# Model untuk update deployment
class DeploymentUpdate(BaseModel):
    replicas: Optional[int] = None
    image: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    


# Model untuk response dari deployment
class DeploymentResponse(BaseModel):
    name: str
    replicas: int
    available: int
    updated: int
    unavailable: int
    labels: Optional[Dict[str, str]] = None
    annotations: dict
    creation_timestamp: str
    namespace: str
    uid: str
    image: Optional[str] = None

class Config:
    orm_mode = True
