from kubernetes import client
from kubernetes.client.rest import ApiException
from app.schemas.cluster_summary import ClusterSummary

def get_cluster_summary() -> ClusterSummary:
    try:
        v1 = client.CoreV1Api()
        
        # Mengambil node
        nodes = v1.list_node()
        
        # Mengambil namespaces
        namespaces = v1.list_namespace()

        # Mengambil versi Kubernetes
        version = client.VersionApi().get_code()

        # Mengembalikan data yang dibutuhkan
        return ClusterSummary(
            node_count=len(nodes.items),
            namespace_count=len(namespaces.items),
            k8s_version=version.git_version
        )
    except ApiException as e:
        raise Exception(f"Error fetching cluster summary: {e}")
