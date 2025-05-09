# app/config/kube_loader.py
from kubernetes import config

def load_kube_config():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
