#!/bin/bash

# Script de entrada para el contenedor ETL
echo "Iniciando contenedor ETL..."

# Iniciar el servicio cron
echo "Iniciando servicio cron..."
service cron start

# Verificar que cron esté funcionando
echo "Estado del servicio cron:"
service cron status

# Mostrar las tareas cron configuradas
echo "Tareas cron configuradas:"
crontab -l

# Ejecutar el proceso ETL una vez al inicio (opcional)
echo "Ejecutando proceso ETL inicial..."
/app/scripts/run_etl.sh

# Healthcheck endpoint simple
echo "Configurando healthcheck..."
python3 -c "
import http.server
import socketserver
import threading

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'ETL Service is running')
        else:
            self.send_response(404)
            self.end_headers()

def start_server():
    with socketserver.TCPServer(('', 8080), HealthHandler) as httpd:
        httpd.serve_forever()

# Iniciar servidor en hilo separado
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()
print('Healthcheck server iniciado en puerto 8080')

# Mantener el contenedor vivo y mostrar logs
import subprocess
import time

while True:
    try:
        # Mostrar logs de cron cada 60 segundos
        time.sleep(60)
        print('=== LOGS DE ETL ===')
        try:
            subprocess.run(['tail', '-n', '10', '/var/log/etl/cron.log'], check=False)
        except:
            pass
    except KeyboardInterrupt:
        break
" &

# Mostrar logs en tiempo real
echo "Mostrando logs en tiempo real..."
tail -f /var/log/etl/cron.log /var/log/etl/etl_process.log /var/log/cron.log