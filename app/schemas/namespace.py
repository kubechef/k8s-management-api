from pydantic import BaseModel, Field
from typing import Dict, List, Optional

# === Base ===
class NamespaceBase(BaseModel):
    name: str
    labels: Optional[Dict[str, str]] = None

class K8snamespace(BaseModel):
    name: str
    status: Optional[str]
    age: Optional[str]
    labels: Optional[Dict[str, str]] = None

class NamespaceCreate(NamespaceBase):
    pass

class NamespaceLabelKeys(BaseModel):
    keys: List[str]

# === Update Namespace Labels ===
class NamespaceLabelUpdate(BaseModel):
    name: str
    labels: Dict[str, str]

# === Resource Quota ===
class ResourceQuotaSpec(BaseModel):
    name: str
    hard: Dict[str, str]

# === Limit Range ===
class LimitItem(BaseModel):
    type: str
    default: Dict[str, str]
    default_request: Dict[str, str]  # snake_case for consistency

class LimitRangeSpec(BaseModel):
    name: str
    limits: List[LimitItem]

# === RBAC ===
class RoleRule(BaseModel):
    api_groups: List[str]  # snake_case for consistency
    resources: List[str]
    verbs: List[str]

class Subject(BaseModel):
    kind: str
    name: str
    api_group: Optional[str] = "rbac.authorization.k8s.io"  # snake_case for consistency

class RBACSpec(BaseModel):
    role_name: str
    rules: List[RoleRule]
    role_binding_name: str
    subjects: List[Subject]
