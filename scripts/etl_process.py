#!/usr/bin/env python3
"""
ETL Process para Data Warehouse
Proceso completo de Extracción, Transformación y Carga
"""
import os
import sys
import logging
from datetime import datetime, date
import sqlalchemy
import pandas as pd
from dotenv import load_dotenv
import time

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/etl/etl_process.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Parámetros de conexión desde variables de entorno
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "qwerty")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "parcial_1")

# URL de conexión
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def wait_for_database():
    """Esperar a que la base de datos esté disponible"""
    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            engine = sqlalchemy.create_engine(DATABASE_URL)
            with engine.connect() as connection:
                connection.execute(sqlalchemy.text("SELECT 1"))
            logger.info("Conexión a la base de datos establecida exitosamente")
            return True
        except Exception as e:
            retry_count += 1
            logger.warning(f"Intento {retry_count}/{max_retries} - Error conectando a DB: {str(e)}")
            time.sleep(2)

    logger.error("No se pudo establecer conexión con la base de datos")
    return False


def create_database_schema():
    """Crear el esquema de la base de datos"""
    try:
        logger.info("Iniciando creación del esquema de base de datos...")

        engine = sqlalchemy.create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # DDL dim_fecha
            connection.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS dim_fecha (
                fecha_key INTEGER PRIMARY KEY,
                fecha_completa DATE NOT NULL,
                anio INTEGER NOT NULL,
                mes INTEGER NOT NULL,
                dia_del_mes INTEGER NOT NULL,
                nombre_mes VARCHAR(20) NOT NULL,
                trimestre INTEGER NOT NULL,
                dia_de_semana INTEGER NOT NULL,
                nombre_dia_semana VARCHAR(20) NOT NULL
            );
            """))

            # DDL dim_cliente
            connection.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS dim_cliente (
                cliente_key SERIAL PRIMARY KEY,
                cliente_id_origen VARCHAR(50) UNIQUE NOT NULL,
                nombre_cliente VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                ciudad VARCHAR(100),
                pais VARCHAR(100),
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """))

            # DDL dim_producto
            connection.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS dim_producto (
                producto_key SERIAL PRIMARY KEY,
                producto_id_origen VARCHAR(50) UNIQUE NOT NULL,
                nombre_producto VARCHAR(255) NOT NULL,
                categoria VARCHAR(100),
                precio_unitario_actual NUMERIC(10, 2),
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """))

            # DDL fact_ventas
            connection.execute(sqlalchemy.text("""
            CREATE TABLE IF NOT EXISTS fact_ventas (
                venta_key BIGSERIAL PRIMARY KEY,
                fecha_key INTEGER NOT NULL,
                cliente_key INTEGER NOT NULL,
                producto_key INTEGER NOT NULL,
                cantidad_vendida INTEGER NOT NULL,
                precio_unitario_en_venta NUMERIC(10, 2) NOT NULL,
                monto_total_venta NUMERIC(12, 2) NOT NULL,
                CONSTRAINT fk_fecha FOREIGN KEY (fecha_key) REFERENCES dim_fecha(fecha_key) ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_cliente FOREIGN KEY (cliente_key) REFERENCES dim_cliente(cliente_key) ON DELETE RESTRICT ON UPDATE CASCADE,
                CONSTRAINT fk_producto FOREIGN KEY (producto_key) REFERENCES dim_producto(producto_key) ON DELETE RESTRICT ON UPDATE CASCADE
            );
            """))

            # Índices
            connection.execute(sqlalchemy.text("""
            CREATE INDEX IF NOT EXISTS idx_fact_ventas_fecha_key ON fact_ventas(fecha_key);
            CREATE INDEX IF NOT EXISTS idx_fact_ventas_cliente_key ON fact_ventas(cliente_key);
            CREATE INDEX IF NOT EXISTS idx_fact_ventas_producto_key ON fact_ventas(producto_key);
            """))

            connection.commit()
            logger.info("Esquema de base de datos creado exitosamente")

    except Exception as e:
        logger.error(f"Error creando esquema de base de datos: {str(e)}")
        raise


def load_csv_data():
    """Cargar datos de los archivos CSV"""
    try:
        logger.info("Iniciando carga de datos CSV...")

        # Verificar si existen los archivos CSV
        csv_files = {
            'clientes': '/app/data/clientes.csv',
            'productos': '/app/data/productos.csv',
            'ventas': '/app/data/ventas_oltp.csv'
        }

        data = {}
        for name, file_path in csv_files.items():
            if os.path.exists(file_path):
                data[name] = pd.read_csv(file_path)
                logger.info(f"Cargado {name}: {len(data[name])} registros")
            else:
                logger.warning(f"Archivo no encontrado: {file_path}")

        return data

    except Exception as e:
        logger.error(f"Error cargando datos CSV: {str(e)}")
        raise


def generate_date_dimension():
    """Generar dimensión de fechas"""
    try:
        logger.info("Generando dimensión de fechas...")

        # Generar fechas desde 2020 hasta 2025
        start_date = date(2020, 1, 1)
        end_date = date(2025, 12, 31)

        dates_data = []
        current_date = start_date

        month_names = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                       'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

        day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        while current_date <= end_date:
            fecha_key = int(current_date.strftime('%Y%m%d'))
            trimestre = (current_date.month - 1) // 3 + 1
            dia_semana = current_date.weekday() + 1  # 1=Lunes, 7=Domingo

            dates_data.append({
                'fecha_key': fecha_key,
                'fecha_completa': current_date,
                'anio': current_date.year,
                'mes': current_date.month,
                'dia_del_mes': current_date.day,
                'nombre_mes': month_names[current_date.month - 1],
                'trimestre': trimestre,
                'dia_de_semana': dia_semana,
                'nombre_dia_semana': day_names[current_date.weekday()]
            })

            # Siguiente día
            from datetime import timedelta
            current_date += timedelta(days=1)

        return pd.DataFrame(dates_data)

    except Exception as e:
        logger.error(f"Error generando dimensión de fechas: {str(e)}")
        raise


def load_dimensions(data):
    """Cargar las dimensiones al Data Warehouse"""
    try:
        logger.info("Cargando dimensiones al Data Warehouse...")

        engine = sqlalchemy.create_engine(DATABASE_URL)

        with engine.connect() as connection:
            # Limpiar tablas en orden correcto (respetando foreign keys)
            logger.info("Limpiando tablas existentes...")
            connection.execute(sqlalchemy.text("DELETE FROM fact_ventas"))
            connection.execute(sqlalchemy.text("DELETE FROM dim_cliente"))
            connection.execute(sqlalchemy.text("DELETE FROM dim_producto"))
            connection.execute(sqlalchemy.text("DELETE FROM dim_fecha"))
            connection.commit()

        # 1. Cargar dim_fecha
        logger.info("Cargando dimensión de fechas...")
        dim_fecha = generate_date_dimension()
        dim_fecha.to_sql('dim_fecha', engine, if_exists='append', index=False, method='multi')
        logger.info(f"Cargados {len(dim_fecha)} registros en dim_fecha")

        # 2. Cargar dim_cliente
        if 'clientes' in data:
            logger.info("Cargando dimensión de clientes...")
            clientes_df = data['clientes'].copy()

            # Transformaciones necesarias - ajustar nombres de columnas
            clientes_df['cliente_id_origen'] = clientes_df['cliente_id'].astype(str)
            clientes_df['nombre_cliente'] = clientes_df['nombre']  # Ajustar nombre de columna
            clientes_df['fecha_carga'] = datetime.now()
            clientes_df['fecha_actualizacion'] = datetime.now()

            # Seleccionar columnas necesarias
            dim_cliente = clientes_df[['cliente_id_origen', 'nombre_cliente', 'email', 'ciudad', 'pais', 'fecha_carga',
                                       'fecha_actualizacion']]

            dim_cliente.to_sql('dim_cliente', engine, if_exists='append', index=False, method='multi')
            logger.info(f"Cargados {len(dim_cliente)} registros en dim_cliente")

        # 3. Cargar dim_producto
        if 'productos' in data:
            logger.info("Cargando dimensión de productos...")
            productos_df = data['productos'].copy()

            # Transformaciones necesarias - ajustar nombres de columnas
            productos_df['producto_id_origen'] = productos_df['producto_id'].astype(str)
            productos_df['precio_unitario_actual'] = productos_df['precio_unitario']  # Ajustar nombre
            productos_df['fecha_carga'] = datetime.now()
            productos_df['fecha_actualizacion'] = datetime.now()

            # Seleccionar columnas necesarias
            dim_producto = productos_df[
                ['producto_id_origen', 'nombre_producto', 'categoria', 'precio_unitario_actual', 'fecha_carga',
                 'fecha_actualizacion']]

            dim_producto.to_sql('dim_producto', engine, if_exists='append', index=False, method='multi')
            logger.info(f"Cargados {len(dim_producto)} registros en dim_producto")

    except Exception as e:
        logger.error(f"Error cargando dimensiones: {str(e)}")
        raise


def load_facts(data):
    """Cargar la tabla de hechos"""
    try:
        if 'ventas' not in data:
            logger.warning("No se encontraron datos de ventas para cargar")
            return

        logger.info("Cargando tabla de hechos...")

        engine = sqlalchemy.create_engine(DATABASE_URL)
        ventas_df = data['ventas'].copy()

        # Obtener las claves de las dimensiones
        with engine.connect() as connection:
            # Mapear clientes
            clientes_map = pd.read_sql("""
                SELECT cliente_key, cliente_id_origen 
                FROM dim_cliente
            """, connection)

            # Mapear productos
            productos_map = pd.read_sql("""
                SELECT producto_key, producto_id_origen 
                FROM dim_producto
            """, connection)

        # Transformar fechas a fecha_key
        ventas_df['fecha_venta'] = pd.to_datetime(ventas_df['fecha_venta'])
        ventas_df['fecha_key'] = ventas_df['fecha_venta'].dt.strftime('%Y%m%d').astype(int)

        # Mapear clientes y productos - ajustar nombres de columnas
        ventas_df['cliente_id_origen'] = ventas_df['cliente_id_fk'].astype(str)  # Ajustar nombre
        ventas_df['producto_id_origen'] = ventas_df['producto_id_fk'].astype(str)  # Ajustar nombre

        # Hacer los joins
        fact_ventas = ventas_df.merge(clientes_map, on='cliente_id_origen', how='inner')
        fact_ventas = fact_ventas.merge(productos_map, on='producto_id_origen', how='inner')

        # Obtener precios de los productos para calcular monto
        with engine.connect() as connection:
            precios_productos = pd.read_sql("""
                SELECT producto_id_origen, precio_unitario_actual 
                FROM dim_producto
            """, connection)

        # Hacer merge con precios
        fact_ventas = fact_ventas.merge(precios_productos, on='producto_id_origen', how='inner')

        # Calcular campos adicionales
        fact_ventas['cantidad_vendida'] = fact_ventas['cantidad']  # Ajustar nombre
        fact_ventas['precio_unitario_en_venta'] = fact_ventas['precio_unitario_actual']
        fact_ventas['monto_total_venta'] = fact_ventas['cantidad_vendida'] * fact_ventas['precio_unitario_en_venta']

        # Seleccionar columnas finales
        fact_final = fact_ventas[[
            'fecha_key', 'cliente_key', 'producto_key',
            'cantidad_vendida', 'precio_unitario_en_venta', 'monto_total_venta'
        ]]

        # Cargar a la base de datos
        fact_final.to_sql('fact_ventas', engine, if_exists='append', index=False, method='multi')
        logger.info(f"Cargados {len(fact_final)} registros en fact_ventas")

    except Exception as e:
        logger.error(f"Error cargando tabla de hechos: {str(e)}")
        raise


def process_etl():
    """Proceso principal de ETL"""
    try:
        logger.info("=== INICIO DEL PROCESO ETL ===")

        # 0. Esperar a que la base de datos esté disponible
        if not wait_for_database():
            raise Exception("No se pudo conectar a la base de datos")

        # 1. Crear esquema
        create_database_schema()

        # 2. Cargar datos CSV
        data = load_csv_data()

        # 3. Cargar dimensiones
        load_dimensions(data)

        # 4. Cargar tabla de hechos
        load_facts(data)

        logger.info("=== PROCESO ETL COMPLETADO EXITOSAMENTE ===")

    except Exception as e:
        logger.error(f"Error en el proceso ETL: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    process_etl()