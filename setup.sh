#!/bin/bash

# Script de inicialización para Disitech Project
# Este script facilita el setup inicial del proyecto

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Disitech Project - Setup Script     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    echo "Por favor instala Docker desde: https://www.docker.com/get-started"
    exit 1
fi

# Verificar que Docker Compose esté instalado
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está instalado${NC}"
    echo "Por favor instala Docker Compose"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker instalado"
echo -e "${GREEN}✓${NC} Docker Compose instalado"
echo ""

# Verificar si existe .env
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ No se encontró archivo .env${NC}"
    echo "Copiando .env.example a .env..."
    cp .env.example .env
    echo -e "${GREEN}✓${NC} Archivo .env creado"
    echo ""
    echo -e "${YELLOW}⚠ IMPORTANTE: Debes editar el archivo .env y configurar:${NC}"
    echo "  - SECRET_KEY (genera una con el comando que se muestra abajo)"
    echo "  - POSTGRES_PASSWORD"
    echo "  - DJANGO_SUPERUSER_* variables"
    echo "  - Credenciales de Bunny Storage (opcional)"
    echo ""
    echo "Para generar un SECRET_KEY ejecuta:"
    echo -e "${GREEN}python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'${NC}"
    echo ""
    read -p "Presiona Enter cuando hayas configurado el archivo .env..."
fi

# Verificar SECRET_KEY
if grep -q "django-insecure-change-me" .env; then
    echo -e "${RED}❌ Debes cambiar el SECRET_KEY en .env${NC}"
    echo "Genera uno nuevo con:"
    echo -e "${GREEN}python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Archivo .env configurado"
echo ""

# Preguntar si quiere construir las imágenes
echo -e "${YELLOW}¿Deseas construir las imágenes de Docker? (s/n)${NC}"
read -p "> " BUILD

if [ "$BUILD" = "s" ] || [ "$BUILD" = "S" ]; then
    echo -e "${GREEN}Construyendo imágenes...${NC}"
    docker-compose build
    echo -e "${GREEN}✓${NC} Imágenes construidas"
fi

echo ""
echo -e "${GREEN}Iniciando servicios...${NC}"
docker-compose up -d

echo ""
echo -e "${GREEN}Esperando a que la base de datos esté lista...${NC}"
sleep 5

echo ""
echo -e "${GREEN}✓${NC} Servicios iniciados correctamente"
echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Setup Completado              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "La aplicación está corriendo en: ${GREEN}http://localhost:8000${NC}"
echo ""
echo "Comandos útiles:"
echo "  ${GREEN}docker-compose logs -f${NC}          Ver logs"
echo "  ${GREEN}docker-compose ps${NC}               Ver estado"
echo "  ${GREEN}docker-compose stop${NC}             Detener servicios"
echo "  ${GREEN}docker-compose down${NC}             Eliminar servicios"
echo "  ${GREEN}docker-compose restart${NC}          Reiniciar servicios"
echo ""
echo "Para crear un backup:"
echo "  ${GREEN}docker-compose exec web python manage.py backup_db${NC}"
echo ""
echo "Para restaurar un backup:"
echo "  ${GREEN}docker-compose exec web python manage.py restore_db${NC}"
echo ""
echo -e "${YELLOW}Credenciales configuradas en .env:${NC}"
echo "  Usuario: $(grep DJANGO_SUPERUSER_USERNAME .env | cut -d '=' -f2)"
echo "  Email: $(grep DJANGO_SUPERUSER_EMAIL .env | cut -d '=' -f2)"
echo ""
