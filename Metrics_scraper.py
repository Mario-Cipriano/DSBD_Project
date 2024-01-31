import docker
from prometheus_client import start_http_server, Gauge
import time
import psutil
import requests
import json
import threading


node_exporter_url = 'http://localhost:9100/metrics'
# Modifica il percorso del socket Docker
docker_socket_path = "unix:///var/run/docker.sock"

# Inizializza il client Docker con il nuovo percorso del socket
client = docker.DockerClient(base_url=docker_socket_path)
containers_cpu_metric = Gauge('docker_container_cpu_usage', 'CPU usage per container', ['container_id', 'container_name'])
database_query_duration=Gauge('database_query_response_time', 'Tempo di risposta delle query del database')
containers_memory_metric = Gauge('docker_container_memory_usage_mb', 'Utilizzo della memoria per container', ['container_id', 'container_name'])
storage_metric = Gauge('storage_usage_percent', 'Percentuale di utilizzo e disponibile dello storage del nodo',['metric_type'])
network_usage = Gauge('network_usage', 'Utilizzo della rete', ['interface', 'direction'])
container_network_metric = Gauge('docker_container_network_usage', 'Utilizzo della rete per container', ['container_id', 'container_name', 'network_interface', 'direction'])

def db_query_duration():
    endpoint=requests.get("http://myweather_handler:3002/metrics")
    if endpoint.status_code==200:
       message=json.dumps(endpoint.json())
       decoded_message=json.loads(message)
       database_query_duration.set(decoded_message["query_duration"])
       
def collect_container_metrics():
    # Ottieni le statistiche sulla CPU del sistema host
    host_cpu_stats = psutil.cpu_times()
    # Calcola il tempo totale della CPU del sistema host in nanosecondi
    host_total_cpu = host_cpu_stats.system+host_cpu_stats.user
    # Ottieni la lista dei container Docker
    try:
     containers = client.containers.list()
    except docker.errors.APIError as e:
     print(f"Error listing containers: {e}")
   
    # Itera attraverso i container e raccogli le metriche
    for container in containers:
        container_id = container.id
        container_name = container.name
        try:
        # Ottieni le statistiche di utilizzo della CPU del container
          stats = container.stats(stream=False)
          cpu_stats = stats['cpu_stats']
          cpu_total_usage = cpu_stats['cpu_usage']['total_usage']
          cpu_system_total = cpu_stats['system_cpu_usage']
          if cpu_system_total > 0:
           cpu_percentage = (cpu_total_usage / cpu_system_total) * 100
           containers_cpu_metric.labels(container_id=container_id, container_name=container_name).set(float(cpu_percentage))
          else:
           print(f"Errore: cpu_system_total è 0 per il container {container_name}")
           # Controlla se la chiave 'memory_stats' è presente nelle statistiche
          if 'memory_stats' in stats:
            memory_stats = stats['memory_stats']
            # Controlla se la chiave 'usage' è presente nelle statistiche sulla memoria
            if 'usage' in memory_stats:
                memory_usage = memory_stats['usage']
                memory_usage_mb = memory_usage / (1024 * 1024) #conversione in megabyte
                containers_memory_metric.labels(container_id=container_id, container_name=container_name).set(memory_usage_mb)
            else:
                print(f"La chiave 'usage' non è presente nelle statistiche sulla memoria per il container {container_name}")
          else:
            print(f"La chiave 'memory_stats' non è presente nelle statistiche per il container {container_name}")

        except docker.errors.APIError as e:
                print(f"Error getting stats for container {container_name}: {e}")
                continue
        
def get_storage_info():
    # Ottieni le informazioni sull'utilizzo dello storage
    storage = psutil.disk_usage('/') 
     # Stampa dettagli per il debug
    print(f'Total: {storage.total} bytes, Used: {storage.used} bytes, Free: {storage.free} bytes, Percent: {storage.percent}%')
      # Calcola la percentuale di utilizzo dello storage
    usage_percentage = storage[3]
    storage_free_mb=storage.free/(1024 * 1024)
    return usage_percentage , storage_free_mb

def update_metrics():
     # Ottieni la percentuale di utilizzo dello storage e lo spazio libero
    storage_usage, storage_free_mb = get_storage_info()
    # Aggiorna la metrica di Prometheus per l'utilizzo dello storage
    storage_metric.labels(metric_type='usage').set(storage_usage)
    # Aggiorna la metrica di Prometheus per lo spazio libero
    storage_metric.labels(metric_type='free').set(storage_free_mb)


# Funzione per raccogliere e esporre le metriche di utilizzo della rete
def collect_network_metrics():
    # Ottieni le informazioni sull'utilizzo della rete
    net_stats = psutil.net_io_counters(pernic=True)
    # Itera attraverso le interfacce di rete
    for interface, stats in net_stats.items():
        # Esponi le metriche per l'invio e la ricezione dei dati
        tx_mb = stats.bytes_sent / (1024 * 1024)
        rx_mb = stats.bytes_recv / (1024 * 1024)
        network_usage.labels(interface=interface, direction='tx').set(tx_mb)
        network_usage.labels(interface=interface, direction='rx').set(rx_mb)

# Funzione per raccogliere e esporre le metriche di utilizzo della rete per ogni container Docker

def collect_container_network_metrics():
    # Ottieni la lista dei container Docker
    try:
        containers = client.containers.list()
    except docker.errors.APIError as e:
        print(f"Error listing containers: {e}")
        return
    # Itera attraverso i container e raccogli le metriche di rete
    for container in containers:
        container_id = container.id
        container_name = container.name
        try:
            # Ottieni le statistiche di rete del container
            stats = container.stats(stream=False)
            # Itera attraverso le interfacce di rete del container
            for interface, interface_stats in stats.get('networks', {}).items():
                tx_bytes = interface_stats['tx_bytes'] 
                rx_bytes = interface_stats['rx_bytes'] 
                # Esponi le metriche di utilizzo della rete per il container
                container_network_metric.labels(
                    container_id=container_id,
                    container_name=container_name,
                    network_interface=interface,
                    direction='tx'
                ).set(tx_bytes)
                container_network_metric.labels(
                    container_id=container_id,
                    container_name=container_name,
                    network_interface=interface,
                    direction='rx'
                ).set(rx_bytes)
        except docker.errors.APIError as e:
            print(f"Error getting network stats for container {container_name}: {e}")


def collect_metrics_thread():
    while True:
        collect_container_metrics()
        update_metrics()
        collect_container_network_metrics()
        collect_network_metrics()
        time.sleep(15)

def db_query_duration_thread():
    while True:
        db_query_duration()
        time.sleep(15)



if __name__ == '__main__':
    # Avvia il server HTTP per esporre le metriche Prometheus
    start_http_server(9100)
    metrics_thread = threading.Thread(target=collect_metrics_thread)
    metrics_thread.start()

    db_query_thread = threading.Thread(target=db_query_duration_thread)
    db_query_thread.start()

  
 




