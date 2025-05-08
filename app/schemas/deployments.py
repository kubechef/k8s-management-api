# Model untuk create deployment
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, Dict

class DeploymentCreate(BaseModel):
    name: str
    namespace: str
    image: str
    replicas: int
    container_port: int
    labels: Optional[Dict[str, str]] = None
    selector: Optional[Dict[str, str]] = None

    @model_validator(mode="after")
    def validate_selector_labels_match(self) -> 'DeploymentCreate':
        if self.labels and self.selector:
            for key, value in self.selector.items():
                if key not in self.labels or self.labels[key] != value:
                    raise ValueError(
                        f"Selector '{key}: {value}' does not match label '{self.labels.get(key)}'"
                    )
        return self


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
