# Dockerfile con cron funcionando
FROM python:3.11-slim

# Instalar dependencias del sistema incluyendo cron
RUN apt-get update && apt-get install -y \
    cron \
    postgresql-client \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p /var/log/etl /app/data /app/scripts

# Copiar archivos del proyecto
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY .env .

# Dar permisos de ejecución a los scripts
RUN chmod +x scripts/etl_process.py
RUN chmod +x scripts/run_etl.sh

# Crear archivos de log
RUN touch /var/log/etl/etl_process.log
RUN touch /var/log/etl/cron.log

# Configurar cron
COPY cron/etl-cron /etc/cron.d/etl-cron
RUN chmod 0644 /etc/cron.d/etl-cron

# Aplicar el archivo cron directamente a root
RUN echo "*/10 * * * * root cd /app && /app/scripts/run_etl.sh >/var/log/etl/cron.log 2>&1" > /etc/cron.d/etl-cron
RUN chmod 0644 /etc/cron.d/etl-cron

# Crear el archivo de log para cron
RUN touch /var/log/cron.log

# Script de entrada
COPY docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]