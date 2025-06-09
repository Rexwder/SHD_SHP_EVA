# 🏗️ ETL Data Warehouse con Docker Compose

Sistema ETL (Extract, Transform, Load) automatizado para Data Warehouse implementado con Docker Compose, PostgreSQL y Python, con ejecución programada mediante cron.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Configuración](#-configuración)
- [Monitoreo](#-monitoreo)
- [Consultas Analíticas](#-consultas-analíticas)
- [Mantenimiento](#-mantenimiento)
- [Troubleshooting](#-troubleshooting)
- [Contribución](#-contribución)

## ✨ Características

- 🐳 **Containerización completa** con Docker Compose
- 🗄️ **Data Warehouse dimensional** con esquema estrella
- 🔄 **ETL automatizado** con ejecución programada (cron)
- 📊 **PostgreSQL** como motor de base de datos
- 📈 **Consultas analíticas** listas para BI
- 📝 **Logging detallado** para monitoreo
- 🔧 **Configuración flexible** via variables de entorno
- 📦 **Datos de ejemplo** incluidos

## 🏛️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Archivos CSV  │───▶│  ETL Processor  │───▶│   PostgreSQL    │
│   (Fuentes)     │    │    (Python)     │    │ (Data Warehouse)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Cron Scheduler │
                       │ (Automatización)│
                       └─────────────────┘
```

### Esquema del Data Warehouse

```
        ┌─────────────┐
        │ dim_fecha   │
        │ fecha_key   │◄─┐
        │ fecha_comp  │  │
        │ anio, mes   │  │
        │ trimestre   │  │
        └─────────────┘  │
                         │
┌─────────────┐         │    ┌─────────────┐
│ dim_cliente │         │    │ dim_producto│
│ cliente_key │◄─┐      │ ┌─▶│ producto_key│
│ nombre      │  │      │ │  │ nombre_prod │
│ email, city │  │      │ │  │ categoria   │
└─────────────┘  │      │ │  │ precio      │
                 │      │ │  └─────────────┘
                 │  ┌───┴─┴──┐
                 └──│fact_ventas│
                    │ fecha_key │
                    │cliente_key│
                    │producto_key│
                    │ cantidad  │
                    │ monto     │
                    └───────────┘
```

## 📋 Requisitos

- Docker Desktop
- Docker Compose
- 4GB RAM disponible
- 2GB espacio en disco

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd SHD_SHP_EVA
```

### 2. Configurar variables de entorno

```bash
# El archivo .env ya está configurado con valores por defecto
# Puedes modificarlo si es necesario
cat .env
```

### 3. Construir y ejecutar

```bash
# Construir contenedores
docker-compose build --no-cache

# Ejecutar en segundo plano
docker-compose up -d

# Verificar estado
docker-compose ps
```

## 🎯 Uso

### Ejecución Automática

El sistema se ejecuta automáticamente cada 10 minutos mediante cron. Para verificar:

```bash
# Ver logs en tiempo real
docker-compose exec etl_processor tail -f /var/log/etl/cron.log

# Verificar estado de cron
docker-compose exec etl_processor service cron status
```

### Ejecución Manual

```bash
# Ejecutar ETL una vez
docker-compose exec etl_processor /app/scripts/run_etl.sh

# Ver resultado
docker-compose exec etl_processor tail -10 /var/log/etl/cron.log
```

### Verificar Datos

```bash
# Contar registros en todas las tablas
docker-compose exec postgres psql -U postgres -d parcial_1 -c "
SELECT 'dim_fecha' as tabla, COUNT(*) as registros FROM dim_fecha
UNION ALL
SELECT 'dim_cliente' as tabla, COUNT(*) as registros FROM dim_cliente  
UNION ALL
SELECT 'dim_producto' as tabla, COUNT(*) as registros FROM dim_producto
UNION ALL
SELECT 'fact_ventas' as tabla, COUNT(*) as registros FROM fact_ventas
ORDER BY tabla;"
```

## 📁 Estructura del Proyecto

```
SHD_SHP_EVA/
├── 📄 docker-compose.yml      # Configuración de servicios
├── 🐳 Dockerfile              # Imagen del ETL processor
├── 🔧 docker-entrypoint.sh    # Script de inicio
├── ⚙️ .env                    # Variables de entorno
├── 📋 requirements.txt        # Dependencias Python
├── 📊 main.ipynb             # Notebook para análisis
├── 📂 data/                  # Archivos CSV fuente
│   ├── clientes.csv
│   ├── productos.csv
│   └── ventas_oltp.csv
├── 📂 scripts/               # Scripts ETL
│   ├── etl_process.py
│   └── run_etl.sh
├── 📂 cron/                  # Configuración cron
│   └── etl-cron
├── 📂 logs/                  # Logs (generado)
└── 📖 README.md              # Este archivo
```

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Base de datos
DB_USER=postgres
DB_PASSWORD=qwerty
DB_HOST=postgres
DB_PORT=5432
DB_NAME=parcial_1

# Logging
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
```

### Configuración de Cron

```bash
# Cambiar frecuencia de ejecución

# Cada 5 minutos (testing)
docker-compose exec etl_processor bash -c "echo '*/5 * * * * root cd /app && /app/scripts/run_etl.sh >/var/log/etl/cron.log 2>&1' > /etc/cron.d/etl-cron"

# Cada hora
docker-compose exec etl_processor bash -c "echo '0 * * * * root cd /app && /app/scripts/run_etl.sh >/var/log/etl/cron.log 2>&1' > /etc/cron.d/etl-cron"

# Diario a las 2 AM (producción)
docker-compose exec etl_processor bash -c "echo '0 2 * * * root cd /app && /app/scripts/run_etl.sh >/var/log/etl/cron.log 2>&1' > /etc/cron.d/etl-cron"

# Reiniciar cron
docker-compose exec etl_processor service cron restart
```

## 📊 Monitoreo

### Logs del Sistema

```bash
# Logs del ETL
docker-compose exec etl_processor tail -f /var/log/etl/etl_process.log

# Logs de cron
docker-compose exec etl_processor tail -f /var/log/etl/cron.log

# Logs de contenedores
docker-compose logs -f etl_processor
docker-compose logs -f postgres
```

### Estado del Sistema

```bash
# Estado de contenedores
docker-compose ps

# Uso de recursos
docker stats

# Estado de servicios
docker-compose exec etl_processor service cron status
docker-compose exec postgres pg_isready -U postgres
```

## 📈 Consultas Analíticas

### Análisis de Ventas por Mes

```sql
SELECT 
    df.nombre_mes,
    COUNT(fv.venta_key) as total_ventas,
    ROUND(SUM(fv.monto_total_venta), 2) as ventas_totales
FROM fact_ventas fv
JOIN dim_fecha df ON fv.fecha_key = df.fecha_key
GROUP BY df.nombre_mes, df.mes
ORDER BY df.mes;
```

### Top Clientes

```sql
SELECT 
    dc.nombre_cliente,
    COUNT(*) as compras,
    ROUND(SUM(fv.monto_total_venta), 2) as total_gastado
FROM fact_ventas fv
JOIN dim_cliente dc ON fv.cliente_key = dc.cliente_key
GROUP BY dc.nombre_cliente
ORDER BY total_gastado DESC
LIMIT 10;
```

### Ventas por Categoría

```sql
SELECT 
    dp.categoria,
    COUNT(*) as ventas,
    ROUND(SUM(fv.monto_total_venta), 2) as total
FROM fact_ventas fv
JOIN dim_producto dp ON fv.producto_key = dp.producto_key
GROUP BY dp.categoria
ORDER BY total DESC;
```

## 🔧 Mantenimiento

### Backup

```bash
# Backup completo
docker-compose exec postgres pg_dump -U postgres parcial_1 > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup solo datos
docker-compose exec postgres pg_dump -U postgres --data-only parcial_1 > data_backup.sql
```

### Limpieza

```bash
# Limpiar solo tabla de hechos
docker-compose exec postgres psql -U postgres -d parcial_1 -c "DELETE FROM fact_ventas;"

# Reiniciar con datos limpios
docker-compose down --volumes
docker-compose up -d
```

### Actualización

```bash
# Reconstruir contenedores
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🐛 Troubleshooting

### Problemas Comunes

#### ETL no ejecuta

```bash
# Verificar logs
docker-compose exec etl_processor cat /var/log/etl/cron.log

# Ejecutar manualmente
docker-compose exec etl_processor /app/scripts/run_etl.sh

# Verificar cron
docker-compose exec etl_processor service cron status
```

#### Sin conexión a BD

```bash
# Verificar PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Ver logs de PostgreSQL
docker-compose logs postgres

# Reiniciar PostgreSQL
docker-compose restart postgres
```

#### Datos no cargan

```bash
# Verificar archivos CSV
docker-compose exec etl_processor ls -la /app/data/

# Ver contenido
docker-compose exec etl_processor head -5 /app/data/clientes.csv

# Verificar permisos
docker-compose exec etl_processor ls -la /app/scripts/
```

### Comandos de Debugging

```bash
# Entrar al contenedor ETL
docker-compose exec etl_processor bash

# Entrar a PostgreSQL
docker-compose exec postgres psql -U postgres -d parcial_1

# Ver configuración
docker-compose exec etl_processor env | grep DB_
docker-compose exec etl_processor cat .env
```

## 📊 Datos de Ejemplo

El sistema incluye datos de ejemplo:

- **100 clientes** con información demográfica
- **100 productos** en 5 categorías
- **100 transacciones** de ventas
- **2,192 fechas** (2020-2025) con dimensiones temporales

### Generar Nuevos Datos

Para generar nuevos datos de prueba, ejecuta en Jupyter:

```python
# Ver el código en main.ipynb para generar datos CSV personalizados
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👥 Autores

- **Tu Nombre** - *Desarrollo inicial* - [TuUsuario](https://github.com/tuusuario)

## 🙏 Agradecimientos

- Docker por la containerización
- PostgreSQL por el motor de base de datos
- Python pandas por el procesamiento de datos
- Cron por la automatización

---

## 🎯 Estado del Proyecto

✅ **Funcional** - Sistema completamente operativo  
✅ **Dockerizado** - Listo para cualquier entorno  
✅ **Automatizado** - ETL programado con cron  
✅ **Monitoreado** - Logs detallados  
✅ **Escalable** - Arquitectura preparada para crecer  

**¡Tu Data Warehouse ETL está listo para producción!** 🚀

# 📚 MANUAL COMPLETO - COMANDOS ETL DATA WAREHOUSE


## 🚀 COMANDOS DE INICIO Y CONFIGURACIÓN

### Construir y ejecutar el sistema
```bash
# Limpiar contenedores previos
docker-compose down --volumes

# Construir desde cero
docker-compose build --no-cache

# Ejecutar en segundo plano
docker-compose up -d
```

### Verificar estado del sistema
```bash
# Ver estado de contenedores
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f etl_processor
docker-compose logs -f postgres
```

---

## 🔍 COMANDOS DE VERIFICACIÓN DE DATOS

### Verificar conteo de registros
```bash
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT 'dim_fecha' as tabla, COUNT(*) as registros FROM dim_fecha UNION ALL SELECT 'dim_cliente' as tabla, COUNT(*) as registros FROM dim_cliente UNION ALL SELECT 'dim_producto' as tabla, COUNT(*) as registros FROM dim_producto UNION ALL SELECT 'fact_ventas' as tabla, COUNT(*) as registros FROM fact_ventas ORDER BY tabla;"
```

### Ver estructura de tablas
```bash
# Ver todas las tablas
docker-compose exec postgres psql -U postgres -d parcial_1 -c "\dt"

# Ver estructura de cada tabla
docker-compose exec postgres psql -U postgres -d parcial_1 -c "\d dim_fecha"
docker-compose exec postgres psql -U postgres -d parcial_1 -c "\d dim_cliente"
docker-compose exec postgres psql -U postgres -d parcial_1 -c "\d dim_producto"
docker-compose exec postgres psql -U postgres -d parcial_1 -c "\d fact_ventas"
```

### Ver datos de ejemplo
```bash
# Ver primeros 5 registros de cada tabla
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT * FROM dim_fecha LIMIT 5;"
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT * FROM dim_cliente LIMIT 5;"
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT * FROM dim_producto LIMIT 5;"
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT * FROM fact_ventas LIMIT 5;"
```

---

## 📊 CONSULTAS ANALÍTICAS

### Análisis de ventas por mes
```bash
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT df.nombre_mes, COUNT(fv.venta_key) as total_ventas, ROUND(SUM(fv.monto_total_venta), 2) as ventas_totales FROM fact_ventas fv JOIN dim_fecha df ON fv.fecha_key = df.fecha_key GROUP BY df.nombre_mes, df.mes ORDER BY df.mes;"
```

### Top 10 clientes por monto gastado
```bash
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT dc.nombre_cliente, COUNT(*) as compras, ROUND(SUM(fv.monto_total_venta), 2) as total_gastado FROM fact_ventas fv JOIN dim_cliente dc ON fv.cliente_key = dc.cliente_key GROUP BY dc.nombre_cliente ORDER BY total_gastado DESC LIMIT 10;"
```

### Ventas por categoría de producto
```bash
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT dp.categoria, COUNT(*) as ventas, ROUND(SUM(fv.monto_total_venta), 2) as total FROM fact_ventas fv JOIN dim_producto dp ON fv.producto_key = dp.producto_key GROUP BY dp.categoria ORDER BY total DESC;"
```

### Análisis por trimestre
```bash
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT df.anio, df.trimestre, COUNT(fv.venta_key) as total_ventas, ROUND(SUM(fv.monto_total_venta), 2) as ventas_totales FROM fact_ventas fv JOIN dim_fecha df ON fv.fecha_key = df.fecha_key GROUP BY df.anio, df.trimestre ORDER BY df.anio, df.trimestre;"
```

### Ventas por día de la semana
```bash
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT df.nombre_dia_semana, COUNT(fv.venta_key) as total_ventas, ROUND(SUM(fv.monto_total_venta), 2) as ventas_totales FROM fact_ventas fv JOIN dim_fecha df ON fv.fecha_key = df.fecha_key GROUP BY df.nombre_dia_semana, df.dia_de_semana ORDER BY df.dia_de_semana;"
```

### Productos más vendidos
```bash
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT dp.nombre_producto, dp.categoria, COUNT(*) as veces_vendido, SUM(fv.cantidad_vendida) as cantidad_total, ROUND(SUM(fv.monto_total_venta), 2) as ingresos_totales FROM fact_ventas fv JOIN dim_producto dp ON fv.producto_key = dp.producto_key GROUP BY dp.nombre_producto, dp.categoria ORDER BY ingresos_totales DESC LIMIT 10;"
```

---

## 🔄 COMANDOS DE GESTIÓN DEL ETL

### Ejecutar ETL manualmente
```bash
# Ejecutar una vez
docker-compose exec etl_processor /app/scripts/run_etl.sh

# Ver resultado de la ejecución
docker-compose exec etl_processor tail -20 /var/log/etl/cron.log
```

### Ver logs del ETL
```bash
# Ver logs más recientes
docker-compose exec etl_processor tail -20 /var/log/etl/etl_process.log

# Ver logs en tiempo real
docker-compose exec etl_processor tail -f /var/log/etl/cron.log

# Ver logs detallados
docker-compose exec etl_processor cat /var/log/etl/etl_process.log
```

---

## ⏰ GESTIÓN DE CRON (AUTOMATIZACIÓN)

### Verificar estado de cron
```bash
# Ver si cron está funcionando
docker-compose exec etl_processor service cron status

# Ver configuración de cron
docker-compose exec etl_processor cat /etc/cron.d/etl-cron

# Ver tareas programadas
docker-compose exec etl_processor crontab -l
```

### Cambiar frecuencia de ejecución
```bash
# Ejecutar cada 2 minutos (para testing)
docker-compose exec etl_processor bash -c "echo '*/2 * * * * root cd /app && /app/scripts/run_etl.sh >/var/log/etl/cron.log 2>&1' > /etc/cron.d/etl-cron"

# Ejecutar cada 5 minutos
docker-compose exec etl_processor bash -c "echo '*/5 * * * * root cd /app && /app/scripts/run_etl.sh >/var/log/etl/cron.log 2>&1' > /etc/cron.d/etl-cron"

# Ejecutar cada hora
docker-compose exec etl_processor bash -c "echo '0 * * * * root cd /app && /app/scripts/run_etl.sh >/var/log/etl/cron.log 2>&1' > /etc/cron.d/etl-cron"

# Ejecutar diariamente a las 2 AM
docker-compose exec etl_processor bash -c "echo '0 2 * * * root cd /app && /app/scripts/run_etl.sh >/var/log/etl/cron.log 2>&1' > /etc/cron.d/etl-cron"

# Reiniciar cron después de cambios
docker-compose exec etl_processor service cron restart
```

---

## 🛠️ COMANDOS DE DEBUGGING Y MANTENIMIENTO

### Entrar al contenedor para debugging
```bash
# Entrar al contenedor ETL
docker-compose exec etl_processor bash

# Entrar al contenedor PostgreSQL
docker-compose exec postgres bash

# Conectar directamente a PostgreSQL
docker-compose exec postgres psql -U postgres -d parcial_1
```

### Verificar archivos CSV
```bash
# Ver archivos disponibles
docker-compose exec etl_processor ls -la /app/data/

# Ver contenido de los archivos
docker-compose exec etl_processor head -5 /app/data/clientes.csv
docker-compose exec etl_processor head -5 /app/data/productos.csv
docker-compose exec etl_processor head -5 /app/data/ventas_oltp.csv
```

### Verificar integridad de datos
```bash
# Verificar que no hay registros huérfanos
docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT 'Ventas sin cliente' as metrica, COUNT(*) as valor FROM fact_ventas fv LEFT JOIN dim_cliente dc ON fv.cliente_key = dc.cliente_key WHERE dc.cliente_key IS NULL UNION ALL SELECT 'Ventas sin producto' as metrica, COUNT(*) as valor FROM fact_ventas fv LEFT JOIN dim_producto dp ON fv.producto_key = dp.producto_key WHERE dp.producto_key IS NULL UNION ALL SELECT 'Ventas sin fecha' as metrica, COUNT(*) as valor FROM fact_ventas fv LEFT JOIN dim_fecha df ON fv.fecha_key = df.fecha_key WHERE df.fecha_key IS NULL;"
```

---

## 💾 COMANDOS DE BACKUP Y RESTAURACIÓN

### Crear backup
```bash
# Backup completo de la base de datos
docker-compose exec postgres pg_dump -U postgres parcial_1 > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup solo de datos
docker-compose exec postgres pg_dump -U postgres --data-only parcial_1 > data_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Limpiar datos
```bash
# Limpiar solo las tablas de hechos (mantener dimensiones)
docker-compose exec postgres psql -U postgres -d parcial_1 -c "DELETE FROM fact_ventas;"

# Limpiar todas las tablas
docker-compose exec postgres psql -U postgres -d parcial_1 -c "DELETE FROM fact_ventas; DELETE FROM dim_cliente; DELETE FROM dim_producto; DELETE FROM dim_fecha;"

# Eliminar y recrear base de datos completa
docker-compose down --volumes
docker-compose up -d
```

---

## 📈 COMANDOS DE MONITOREO

### Ver recursos utilizados
```bash
# Ver uso de recursos
docker stats

# Ver logs del sistema
docker-compose logs --tail=50 etl_processor
docker-compose logs --tail=50 postgres
```

### Healthcheck
```bash
# Verificar que los servicios responden
curl -f http://localhost:8080/health || echo "ETL service not responding"

# Verificar conexión a base de datos
docker-compose exec postgres pg_isready -U postgres
```

---

## 🔧 COMANDOS DE CONFIGURACIÓN AVANZADA

### Variables de entorno
```bash
# Ver variables de entorno del contenedor
docker-compose exec etl_processor env | grep DB_

# Verificar configuración
docker-compose exec etl_processor cat .env
```

### Reiniciar servicios
```bash
# Reiniciar solo ETL
docker-compose restart etl_processor

# Reiniciar solo PostgreSQL
docker-compose restart postgres

# Reiniciar todo
docker-compose restart
```

---

## 🎯 COMANDOS DE VERIFICACIÓN RÁPIDA

### Verificación completa en un comando
```bash
# Script de verificación rápida
docker-compose ps && echo "=== DATOS ===" && docker-compose exec postgres psql -U postgres -d parcial_1 -c "SELECT 'dim_fecha' as tabla, COUNT(*) as registros FROM dim_fecha UNION ALL SELECT 'dim_cliente' as tabla, COUNT(*) as registros FROM dim_cliente UNION ALL SELECT 'dim_producto' as tabla, COUNT(*) as registros FROM dim_producto UNION ALL SELECT 'fact_ventas' as tabla, COUNT(*) as registros FROM fact_ventas ORDER BY tabla;" && echo "=== CRON ===" && docker-compose exec etl_processor service cron status
```

---

## 🏁 COMANDOS DE PARADA Y LIMPIEZA

### Parar el sistema
```bash
# Parar contenedores (mantener datos)
docker-compose stop

# Parar y eliminar contenedores (mantener datos)
docker-compose down

# Parar y eliminar todo (incluyendo datos)
docker-compose down --volumes

# Limpiar imágenes Docker
docker system prune -a
```

---

**🎉 ¡Tu sistema ETL está completamente funcional con estos comandos!**