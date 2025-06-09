#!/bin/bash

# Script para ejecutar el proceso ETL
# Este script será llamado por cron

# Configurar PATH para cron
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PYTHONPATH=/usr/local/lib/python3.11/site-packages

echo "$(date): === INICIANDO PROCESO ETL ===" >> /var/log/etl/cron.log

# Cambiar al directorio de la aplicación
cd /app

# Verificar que existan los archivos necesarios
if [ ! -f "scripts/etl_process.py" ]; then
    echo "$(date): ERROR - No se encuentra el archivo etl_process.py" >> /var/log/etl/cron.log
    exit 1
fi

if [ ! -d "data" ]; then
    echo "$(date): ERROR - No se encuentra el directorio data" >> /var/log/etl/cron.log
    exit 1
fi

# Verificar conexión a la base de datos usando el path completo de python
echo "$(date): Verificando conexión a la base de datos..." >> /var/log/etl/cron.log
/usr/local/bin/python3 -c "
import os
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'qwerty')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'parcial_1')

DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = sqlalchemy.create_engine(DATABASE_URL)
with engine.connect() as connection:
    connection.execute(sqlalchemy.text('SELECT 1'))
print('Conexión a BD exitosa')
" >> /var/log/etl/cron.log 2>&1

if [ $? -ne 0 ]; then
    echo "$(date): ERROR - No se pudo conectar a la base de datos" >> /var/log/etl/cron.log
    exit 1
fi

# Ejecutar el proceso ETL usando el path completo
echo "$(date): Ejecutando proceso ETL..." >> /var/log/etl/cron.log
/usr/local/bin/python3 scripts/etl_process.py >> /var/log/etl/cron.log 2>&1

# Verificar el resultado
ETL_EXIT_CODE=$?
if [ $ETL_EXIT_CODE -eq 0 ]; then
    echo "$(date): === PROCESO ETL COMPLETADO EXITOSAMENTE ===" >> /var/log/etl/cron.log
else
    echo "$(date): === ERROR EN EL PROCESO ETL (Exit Code: $ETL_EXIT_CODE) ===" >> /var/log/etl/cron.log
    exit $ETL_EXIT_CODE
fi

# Mostrar estadísticas básicas
echo "$(date): Generando estadísticas del proceso..." >> /var/log/etl/cron.log
/usr/local/bin/python3 -c "
import os
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'qwerty')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'parcial_1')

DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = sqlalchemy.create_engine(DATABASE_URL)

with engine.connect() as connection:
    # Contar registros en cada tabla
    dim_fecha_count = connection.execute(sqlalchemy.text('SELECT COUNT(*) FROM dim_fecha')).scalar()
    dim_cliente_count = connection.execute(sqlalchemy.text('SELECT COUNT(*) FROM dim_cliente')).scalar()
    dim_producto_count = connection.execute(sqlalchemy.text('SELECT COUNT(*) FROM dim_producto')).scalar()
    fact_ventas_count = connection.execute(sqlalchemy.text('SELECT COUNT(*) FROM fact_ventas')).scalar()

    print(f'Estadísticas del Data Warehouse:')
    print(f'- dim_fecha: {dim_fecha_count} registros')
    print(f'- dim_cliente: {dim_cliente_count} registros')
    print(f'- dim_producto: {dim_producto_count} registros')
    print(f'- fact_ventas: {fact_ventas_count} registros')
" >> /var/log/etl/cron.log 2>&1

echo "$(date): === FIN DEL PROCESO ETL ===" >> /var/log/etl/cron.log