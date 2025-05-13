from pydantic import BaseModel

class ClusterSummary(BaseModel):
    node_count: int
    namespace_count: int
    k8s_version: str
