from pydantic import BaseModel, Field
from typing import Optional, Dict
from fastapi import UploadFile

# Schema untuk menerima payload ketika membuat ConfigMap dengan file
class ConfigMapCreateFile(BaseModel):
    name: str
    namespace: str
    file: UploadFile  # Ini akan menerima file dari form-data

# Schema untuk menerima payload ketika membuat ConfigMap dengan teks
class ConfigMapCreateText(BaseModel):
    name: str
    namespace: str
    content: str  # Ini akan menerima teks dari body request


class ConfigMapResponse(BaseModel):
    name: str
    namespace: str
    data: Dict[str, str]
    message: str

# schemas/configmap.py
class ConfigMapListItem(BaseModel):
    name: str
    namespace: str
    data: Optional[dict] = None

# schemas/configmap.py
class ConfigMapSingleItem(BaseModel):
    name: str
    namespace: str
    data: Optional[dict] = None

