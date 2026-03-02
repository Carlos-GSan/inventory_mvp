.PHONY: help setup build up down restart logs shell migrate backup restore superuser clean

help:
	@echo "Disitech Project - Comandos disponibles:"
	@echo ""
	@echo "  make setup          - Configuración inicial del proyecto"
	@echo "  make build          - Construir imágenes Docker"
	@echo "  make up             - Iniciar servicios"
	@echo "  make down           - Detener servicios"
	@echo "  make restart        - Reiniciar servicios"
	@echo "  make logs           - Ver logs en tiempo real"
	@echo "  make shell          - Acceder al shell del contenedor web"
	@echo "  make migrate        - Ejecutar migraciones"
	@echo "  make backup         - Crear backup de base de datos"
	@echo "  make restore        - Restaurar backup de base de datos"
	@echo "  make superuser      - Crear/verificar superusuario"
	@echo "  make clean          - Limpiar contenedores y volúmenes"
	@echo ""

setup:
	@./setup.sh

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "✓ Servicios iniciados en http://localhost:8000"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

shell:
	docker-compose exec web bash

migrate:
	docker-compose exec web python manage.py migrate

backup:
	docker-compose exec web python manage.py backup_db
	@echo "✓ Backup creado en backups/"

restore:
	@echo "Restaurando desde backup.json..."
	docker-compose exec web python manage.py restore_db

superuser:
	docker-compose exec web python manage.py ensure_superuser

clean:
	docker-compose down -v
	@echo "⚠ Contenedores y volúmenes eliminados"

# Comandos para desarrollo local (sin Docker)
dev-install:
	uv sync

dev-migrate:
	uv run manage.py migrate

dev-run:
	uv run manage.py runserver

dev-backup:
	uv run manage.py backup_db

dev-restore:
	uv run manage.py restore_db

dev-superuser:
	uv run manage.py ensure_superuser
