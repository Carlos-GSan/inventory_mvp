# Disitech Project - Guía de Despliegue

Sistema de gestión empresarial con Django, PostgreSQL y Bunny Storage.

## 📋 Características

- ✅ Django 6.0 con Python 3.12
- ✅ PostgreSQL como base de datos en producción
- ✅ Bunny CDN Storage para archivos media
- ✅ Nombres de archivos SEO-friendly automáticos
- ✅ Docker y Docker Compose para despliegue
- ✅ Backup y restore de base de datos
- ✅ Creación automática de superusuario

## 🚀 Inicio Rápido con Docker

### 1. Clonar y configurar el proyecto

```bash
# Clonar el repositorio
git clone <tu-repositorio>
cd disitech_project

# Copiar archivo de configuración
cp .env.example .env
```

### 2. Configurar variables de entorno

Edita el archivo `.env` con tus credenciales:

```bash
# Requerido: Cambiar SECRET_KEY
SECRET_KEY=tu-clave-secreta-super-segura

# Configurar base de datos
POSTGRES_PASSWORD=tu-password-seguro

# Configurar superusuario inicial
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@tudominio.com
DJANGO_SUPERUSER_PASSWORD=password-seguro

# (Opcional) Configurar Bunny Storage
USE_BUNNY_STORAGE=True
BUNNY_STORAGE_ACCESS_KEY=tu-access-key
BUNNY_STORAGE_ZONE=tu-storage-zone
BUNNY_HOSTNAME=tu-cdn.b-cdn.net
BUNNY_TOKEN_KEY=tu-token-key
```

### 3. Generar SECRET_KEY

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 4. Levantar con Docker Compose

```bash
# Construir y levantar servicios
docker-compose up -d --build

# Ver logs
docker-compose logs -f web

# El superusuario se crea automáticamente en el primer inicio
```

La aplicación estará disponible en: http://localhost:8000

## 💻 Desarrollo Local (sin Docker)

### 1. Instalar dependencias

```bash
# Instalar uv (gestor de paquetes)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias
uv sync
```

### 2. Configurar para desarrollo

```bash
# Copiar .env.example
cp .env.example .env

# Editar .env para desarrollo
# Cambiar: USE_POSTGRES=False (para usar SQLite)
# Cambiar: DEBUG=True
```

### 3. Ejecutar migraciones y crear superusuario

```bash
# Aplicar migraciones
uv run manage.py migrate

# Crear superusuario (si no existe ningún usuario)
uv run manage.py ensure_superuser

# O crear manualmente
uv run manage.py createsuperuser
```

### 4. Ejecutar servidor de desarrollo

```bash
uv run manage.py runserver
```

## 🗄️ Comandos de gestión

### Backup de base de datos

```bash
# Crear backup (excluye usuarios)
uv run manage.py backup_db

# Crear backup en ubicación específica
uv run manage.py backup_db -o respaldos/

# Sin copia versionada
uv run manage.py backup_db --no-version
```

Los backups se guardan en:
- `backup.json` - Archivo principal
- `backups/backup_YYYYMMDD_HHMMSS.json` - Copias versionadas

### Restaurar base de datos

```bash
# Restaurar desde backup.json
uv run manage.py restore_db

# Restaurar desde archivo específico
uv run manage.py restore_db -i backups/backup_20260301_120000.json

# Ejecutar migraciones antes de restaurar
uv run manage.py restore_db --run-migrations

# Limpiar datos antes (excepto usuarios)
uv run manage.py restore_db --flush
```

### Crear superusuario automáticamente

```bash
# Solo crea si no existe ningún usuario
uv run manage.py ensure_superuser
```

Usa las variables de entorno:
- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_EMAIL`
- `DJANGO_SUPERUSER_PASSWORD`

## 📁 Archivos con nombres SEO-friendly

Los archivos subidos automáticamente se renombran a formato SEO-friendly:

```python
# Ejemplo: "Mi Foto Año 2024.JPG"
# Se convierte en: "mi-foto-ano-2024-a1b2c3d4.jpg"

from apps.common.utils import generate_unique_filename

class MiModelo(models.Model):
    archivo = models.FileField(
        upload_to=lambda instance, filename: generate_unique_filename(
            instance, filename, "carpeta_destino"
        )
    )
```

Características:
- ✅ Elimina acentos y caracteres especiales
- ✅ Convierte a minúsculas
- ✅ Reemplaza espacios por guiones
- ✅ Agrega UUID corto para garantizar unicidad
- ✅ Mantiene extensión original

## 🔧 Configuración de Bunny Storage

### 1. Crear cuenta en Bunny.net

1. Registrarse en https://bunny.net
2. Crear un Storage Zone
3. Obtener Access Key desde el panel

### 2. Configurar CDN (opcional pero recomendado)

1. Crear un Pull Zone vinculado al Storage Zone
2. Habilitar Token Authentication en el Pull Zone
3. Copiar el Token Authentication Key

### 3. Configurar en .env

```bash
USE_BUNNY_STORAGE=True
BUNNY_STORAGE_ACCESS_KEY=tu-access-key-del-storage-zone
BUNNY_STORAGE_ZONE=nombre-del-storage-zone
BUNNY_HOSTNAME=tu-pullzone.b-cdn.net
BUNNY_TOKEN_KEY=tu-token-authentication-key
```

## 🐳 Comandos Docker útiles

```bash
# Ver servicios corriendo
docker-compose ps

# Ver logs
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Parar servicios
docker-compose stop

# Eliminar todo (¡cuidado! elimina datos)
docker-compose down -v

# Acceder al contenedor web
docker-compose exec web bash

# Ejecutar comandos Django
docker-compose exec web python manage.py <comando>

# Backup de base de datos
docker-compose exec web python manage.py backup_db

# Restore de base de datos
docker-compose exec web python manage.py restore_db
```

## 📦 Estructura del proyecto

```
disitech_project/
├── apps/
│   ├── common/           # Utilidades comunes
│   │   ├── bunny.py      # Integración Bunny CDN
│   │   ├── utils.py      # Utilidades generales
│   │   └── management/commands/
│   │       ├── backup_db.py
│   │       ├── restore_db.py
│   │       └── ensure_superuser.py
│   ├── inventory/        # Gestión de inventario
│   └── profiles/         # Perfiles de empleados
├── config/               # Configuración Django
├── static/              # Archivos estáticos
├── templates/           # Plantillas HTML
├── docker-compose.yml   # Configuración Docker
├── Dockerfile           # Imagen Docker
├── .env.example         # Ejemplo de variables
└── pyproject.toml       # Dependencias Python
```

## 🔒 Seguridad en Producción

Asegúrate de configurar en `.env`:

```bash
DEBUG=False
SECRET_KEY=<clave-segura-generada>
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
```

El proyecto automáticamente habilita en producción (DEBUG=False):
- ✅ HTTPS redirect
- ✅ Secure cookies
- ✅ XSS protection
- ✅ Content type sniffing protection

## 📝 Licencia

[Tu licencia aquí]

## 🤝 Contribuir

[Instrucciones de contribución]

## 📞 Soporte

[Información de contacto]
