from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class K8sEvent(BaseModel):
    type: Optional[str]
    reason: Optional[str]
    message: Optional[str]
    involved_object: Optional[str]
    source: Optional[str]
    timestamp: datetime
