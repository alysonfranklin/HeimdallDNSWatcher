import os
import logging
from kubernetes import client, config, watch
import requests

# Configuração de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

# Configurações e variáveis sensíveis
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN').strip()
CLOUDFLARE_ZONE_ID = os.getenv('CLOUDFLARE_ZONE_ID').strip()
CLOUDFLARE_API_BASE = 'https://api.cloudflare.com/client/v4/zones'
TARGET_CNAME_ADDRESS = os.getenv('TARGET_CNAME_ADDRESS')

# Carregar configuração do Kubernetes
config.load_incluster_config()  # Use load_kube_config() para testes locais
custom_api = client.CustomObjectsApi()

def determine_proxy_status(labels):
    # Obter o valor da label 'proxyEnabled' como string, padrão para 'true'
    proxy_enabled = labels.get('proxyEnabled', 'true').lower()
    return proxy_enabled == 'true'

def update_dns_record(record_id, name, content, app_label, proxied):
    update_url = f"{CLOUDFLARE_API_BASE}/{CLOUDFLARE_ZONE_ID}/dns_records/{record_id}"
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'type': 'CNAME',
        'name': name,
        'content': content,
        'ttl': 1,  # TTL "Auto"
        'proxied': proxied,
        'comment': app_label
    }
    update_response = requests.put(update_url, json=data, headers=headers)
    if update_response.status_code == 200:
        logger.info(f"Successfully updated DNS record: {name} with proxy {'enabled' if proxied else 'disabled'}.")
    else:
        logger.error(f"Failed to update DNS record: {name} - {update_response.text}")

def create_dns_record(name, content, app_label, proxied):
    url = f"{CLOUDFLARE_API_BASE}/{CLOUDFLARE_ZONE_ID}/dns_records"
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'type': 'CNAME',
        'name': name,
        'content': content,
        'ttl': 1,  # TTL "Auto"
        'proxied': proxied,
        'comment': app_label
    }
    create_response = requests.post(url, json=data, headers=headers)
    if create_response.status_code == 200:
        logger.info(f"Successfully created DNS record: {name} with proxy {'enabled' if proxied else 'disabled'}.")
    else:
        logger.error(f"Failed to create DNS record: {name} - {create_response.text}")

def delete_dns_record(record_id, name):
    logger.info(f"Attempting to delete DNS record: {name}")
    delete_url = f"{CLOUDFLARE_API_BASE}/{CLOUDFLARE_ZONE_ID}/dns_records/{record_id}"
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    delete_response = requests.delete(delete_url, headers=headers)
    if delete_response.status_code == 200:
        logger.info(f"Successfully deleted DNS record: {name}")
    else:
        logger.error(f"Failed to delete DNS record: {name} - {delete_response.text}")

def handle_ingressroute_event(event):
    ingressroute = event['object']
    metadata = ingressroute.get('metadata', {})
    labels = metadata.get('labels', {})
    
    if labels.get('dns') == 'cloudflare':
        app_label = labels.get('app', 'unknown-app')
        proxied = determine_proxy_status(labels)

        # Obtenha o host a partir do IngressRoute
        new_host = ingressroute['spec']['routes'][0]['match'].split('`')[1]

        # Buscar registros DNS existentes com o nome (host) e label "app"
        list_url = f"{CLOUDFLARE_API_BASE}/{CLOUDFLARE_ZONE_ID}/dns_records?name={new_host}&type=CNAME"
        headers = {
            'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        response = requests.get(list_url, headers=headers)
        if response.status_code == 200:
            records = response.json().get('result', [])
            existing_record = next((record for record in records if record['name'] == new_host and record.get('comment') == app_label), None)
        else:
            logger.error(f"Failed to fetch DNS records: {response.text}")
            return

        # Lidar com eventos 'ADDED' ou 'MODIFIED'
        match event['type']:
            case 'ADDED', 'MODIFIED':
                if existing_record:
                    # Verifique se o host mudou e, se sim, atualize o registro
                    logger.info(f"IngressRoute modified: {metadata.get('name')} - Updating DNS record for host {new_host}.")
                    update_dns_record(existing_record['id'], new_host, TARGET_CNAME_ADDRESS, app_label, proxied)
                else:
                    # Se não houver um registro correspondente, crie um novo
                    logger.info(f"IngressRoute added: {new_host}")
                    create_dns_record(new_host, TARGET_CNAME_ADDRESS, app_label, proxied)

            # Lidar com eventos 'DELETED'
            case 'DELETED':
                if existing_record:
                    logger.info(f"IngressRoute deleted: {metadata.get('name')} - Deleting DNS record {existing_record['name']}")
                    delete_dns_record(existing_record['id'], existing_record['name'])
                else:
                    logger.warning(f"No existing DNS record found for deleted IngressRoute: {metadata.get('name')}")

def main():
    logger.info("Starting IngressRoute DNS Manager")
    w = watch.Watch()
    try:
        for event in w.stream(custom_api.list_cluster_custom_object,
                              group="traefik.containo.us", version="v1alpha1", plural="ingressroutes"):
            handle_ingressroute_event(event)
    except Exception as e:
        logger.error(f"Error watching IngressRoutes: {e}")

if __name__ == '__main__':
    main()