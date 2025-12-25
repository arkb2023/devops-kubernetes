#!/usr/bin/env python3
import time
import logging
import requests
from kubernetes import client, config, watch

# Structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def resource_names(name):
    return {
        "configmap": f"ds-cm-{name}",
        "deployment": f"ds-deploy-{name}", 
        "service": f"ds-svc-{name}",
        "labels": {"app": f"ds-{name}"}
    }

def deploy_nginx_site(name):
    names = resource_names(name)
    
    # ConfigMap volume reference
    cm_volume = {
        "name": "html",
        "configMap": {"name": names["configmap"]}
    }
    
    # Deployment
    deployment_spec = {
        "metadata": {"name": names["deployment"], "namespace": "default"},
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": names["labels"]},
            "template": {
                "metadata": {"labels": names["labels"]},
                "spec": {
                    "containers": [{
                        "name": "nginx",
                        "image": "nginx:alpine",
                        "ports": [{"containerPort": 80}],
                        "volumeMounts": [{"name": "html", "mountPath": "/usr/share/nginx/html"}]
                    }],
                    "volumes": [cm_volume]
                }
            }
        }
    }
    
    # Service
    service_spec = {
        "metadata": {"name": names["service"], "namespace": "default"},
        "spec": {
            "selector": names["labels"],
            "ports": [{"port": 80, "targetPort": 80}]
        }
    }

    try:
        # Deploy
        apps_api = client.AppsV1Api()
        deployment = client.V1Deployment(**deployment_spec)
        apps_api.create_namespaced_deployment("default", deployment)
        logger.info(f"Deployment '{names['deployment']}' created")
    except Exception as e:
        if e.status != 409:  # Ignore "already exists"
            logger.error(f"Deployment error: {e}")
            return False
        logger.info(f"Deployment '{names['deployment']}' already exists!")
    
    try:
        core_api = client.CoreV1Api()
        service = client.V1Service(**service_spec)
        core_api.create_namespaced_service("default", service)
        logger.info(f"Service '{names['service']}' created")
    except Exception as e:
        if e.status != 409:  # Ignore "already exists"
            logger.error(f"❌ Service error: {e}")
            return False
        logger.info(f"Service '{names['service']}' already exists!")

    logger.info(f"Nginx stack '{names['deployment']}' deployed!")
    return True

def get_name(obj):
    """Handle both object types"""
    try:
        if hasattr(obj, 'metadata') and hasattr(obj.metadata, 'name'):
            return obj.metadata.name
        elif isinstance(obj, dict) and 'metadata' in obj and 'name' in obj['metadata']:
            return obj['metadata']['name']
        return str(obj)[:30]
    except:
        return "unknown"

def create_configmap(name, website_url):
    """Create or update ConfigMap"""
    names = resource_names(name)
    cm_name = names["configmap"]
    try:
        logger.info(f"Fetching {website_url}...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        #resp = requests.get(website_url, timeout=10)
        resp = requests.get(website_url, timeout=10, headers=headers)
        resp.raise_for_status()
        #html = resp.text[:5000]
        logger.info(f"resp.text len {len(resp.text)}")
        html = resp.text[:400000]
        
        core_api = client.CoreV1Api()
        
        # Check if exists first
        try:
            existing = core_api.read_namespaced_config_map(cm_name, "default")
            logger.info(f"Updating ConfigMap {cm_name}")
            existing.data["index.html"] = html
            core_api.patch_namespaced_config_map(cm_name, "default", existing)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                # Create new
                logger.info(f"Creating new ConfigMap {cm_name}")
                configmap = client.V1ConfigMap(
                    metadata=client.V1ObjectMeta(
                        name=cm_name,
                        namespace="default",
                        labels=names["labels"]
                    ),
                    data={"index.html": html}
                )
                core_api.create_namespaced_config_map("default", configmap)
            else:
                raise e

        logger.info(f"ConfigMap {cm_name} ready ({len(html)} bytes)")
        return True
        
    except Exception as e:
        logger.error(f"ConfigMap error: {e}")
        return False


def main():
    logger.info("Loading in-cluster config...")
    config.load_incluster_config()
    logger.info("config.load_incluster_config() OK")
    
    custom_api = client.CustomObjectsApi()
    logger.info("client.CustomObjectsApi() OK")

    GROUP, VERSION, PLURAL, NAMESPACE = "stable.dwk", "v1", "dummysites", "default"
    logger.info(f"DummySite Controller watching {NAMESPACE}...")
    
    # List existing
    try:
        resp = custom_api.list_namespaced_custom_object(GROUP, VERSION, NAMESPACE, PLURAL)
        logger.info(f"Found {len(resp.items())} existing DummySites")
    except Exception as e:
        logger.warning(f"List error: {e}")
    
    logger.info("Watch stream + ConfigMap creation...")

    loop_counter = 0
    while True:
        loop_counter += 1
        logger.info(f"Watch loop #{loop_counter} (timeout=30s)")
        try:
            w = watch.Watch()
            event_count = 0
            for event in w.stream(
                custom_api.list_namespaced_custom_object, 
                GROUP, VERSION, NAMESPACE, PLURAL, 
                timeout_seconds=30
            ):
                event_count += 1

                event_type = event['type']
                obj = event['object']
                name = get_name(obj)

                logger.info(f"EVENT #{event_count}: {event_type} '{name}'")

                if event_type == 'ADDED':
                    logger.info(f"Processing DummySite '{name}'...")
                    # Get full object details
                    full_obj = custom_api.get_namespaced_custom_object(
                        GROUP, VERSION, "default", PLURAL, name)
                    url = full_obj['spec']['website_url']

                    # STATUS CHECK
                    if full_obj.get('status', {}).get('deployed'):
                        logger.info(f"'{name}' already deployed (status)!")
                    else:  
                        # Create ConfigMap with HTML
                        if create_configmap(name, url):
                            logger.info(f"DummySite '{name}' COMPLETE!")
                            if deploy_nginx_site(name):
                                # MARK COMPLETE
                                full_obj['status'] = {'deployed': True}
                                custom_api.patch_namespaced_custom_object(
                                GROUP, VERSION, NAMESPACE, PLURAL, name, full_obj)
                                logger.info(f"COMPLETE DummySite '{name}'!")
                            else:
                                logger.error(f"deploy_nginx_site failed for '{name}'")
                        else:
                            logger.error(f"create_configmap failed for '{name}'")
                elif event_type == 'DELETED':
                    logger.info(f"Deletion '{name}' (cleanup not implemented)")
                else:
                    logger.debug(f"Skipped '{event_type}' event")

            # HEARTBEAT
            if event_count > 0:
                logger.info(f"Processed {event_count} events in loop #{loop_counter}")
            else:
                logger.info(f"No events in 30s (loop #{loop_counter})")

        except KeyboardInterrupt:
            logger.info("Shutdown")
            break

        except Exception as e:
            logger.error(f"Watch error: {e}")
            logger.info("Reconnecting in 5s...")
            time.sleep(5)

if __name__ == '__main__':
    logger.info("=== STARTING DummySite Controller ===")
    main()
    logger.info("=== STOPPING DummySite Controller ===")
