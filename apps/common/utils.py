"""
Utilidades comunes para el proyecto.
"""
import os
import re
import uuid
from pathlib import Path
from unicodedata import normalize, category as unicode_category


def normalize_name(value: str) -> str:
    """
    Normaliza un nombre para comparaciones case-insensitive y sin acentos.

    Convierte a minúsculas, elimina acentos/diacríticos y colapsa
    espacios múltiples en uno solo.

    Esto permite tratar "Herramienta", "herramienta", "HERRAMIENTA"
    y "herramientá" como equivalentes.

    Args:
        value: Texto a normalizar.

    Returns:
        Texto normalizado listo para comparación.

    Examples:
        >>> normalize_name("Herramienta")
        'herramienta'
        >>> normalize_name("HERRAMIENTA")
        'herramienta'
        >>> normalize_name("  Tornillo   Galvanizado  ")
        'tornillo galvanizado'
        >>> normalize_name("Válvula de Presión")
        'valvula de presion'
    """
    if not value:
        return ""
    # Descomponer unicode (NFD) para separar caracteres base de diacríticos
    decomposed = normalize('NFD', value)
    # Filtrar marcas diacríticas (categoría unicode 'Mn' = Mark, Nonspacing)
    stripped = ''.join(c for c in decomposed if unicode_category(c) != 'Mn')
    # Minúsculas
    lowered = stripped.lower()
    # Colapsar espacios múltiples y strip
    cleaned = re.sub(r'\s+', ' ', lowered).strip()
    return cleaned


def slugify_filename(filename: str) -> str:
    """
    Convierte un nombre de archivo a un formato SEO-friendly (slug).
    
    Mantiene la extensión del archivo original.
    Elimina acentos, espacios y caracteres especiales.
    Convierte a minúsculas.
    
    Args:
        filename: Nombre del archivo original (puede incluir path)
    
    Returns:
        Nombre de archivo limpio y SEO-friendly
        
    Examples:
        >>> slugify_filename("Mi Foto Año 2024.jpg")
        'mi-foto-ano-2024.jpg'
        >>> slugify_filename("Cotización #123.PDF")
        'cotizacion-123.pdf'
    """
    # Extraer nombre y extensión
    name, ext = os.path.splitext(filename)
    
    # Normalizar unicode (quitar acentos)
    name = normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    
    # Convertir a minúsculas
    name = name.lower()
    
    # Reemplazar espacios y guiones bajos por guiones
    name = name.replace(' ', '-').replace('_', '-')
    
    # Quitar caracteres especiales (solo permitir letras, números y guiones)
    name = re.sub(r'[^a-z0-9\-]', '', name)
    
    # Quitar guiones múltiples
    name = re.sub(r'\-+', '-', name)
    
    # Quitar guiones al inicio y final
    name = name.strip('-')
    
    # Si el nombre quedó vacío, usar un UUID
    if not name:
        name = str(uuid.uuid4())[:8]
    
    # Convertir extensión a minúsculas
    ext = ext.lower()
    
    return f"{name}{ext}"


def generate_unique_filename(instance, filename: str, field_name: str = "file") -> str:
    """
    Genera un nombre de archivo único y SEO-friendly para un modelo de Django.
    
    Útil para usar en upload_to de FileField/ImageField.
    Combina el nombre slugificado con un UUID corto para garantizar unicidad.
    
    Args:
        instance: Instancia del modelo
        filename: Nombre del archivo original
        field_name: Nombre del campo (opcional, para subdirectorios)
    
    Returns:
        Ruta relativa para el archivo
        
    Example:
        class Employee(models.Model):
            photo = models.ImageField(
                upload_to=lambda instance, filename: generate_unique_filename(
                    instance, filename, "employee_photos"
                )
            )
    """
    # Obtener nombre slugificado
    slug_name = slugify_filename(filename)
    
    # Separar nombre y extensión
    name, ext = os.path.splitext(slug_name)
    
    # Generar UUID corto (8 caracteres)
    unique_id = str(uuid.uuid4())[:8]
    
    # Combinar: nombre-uuid.ext
    unique_name = f"{name}-{unique_id}{ext}"
    
    # Retornar path completo
    # Si la instancia tiene un modelo específico, usar su nombre
    if hasattr(instance, '_meta'):
        model_name = instance._meta.model_name
        return os.path.join(field_name, model_name, unique_name)
    
    return os.path.join(field_name, unique_name)


def rename_file_seo_friendly(file_path: str) -> str:
    """
    Renombra un archivo existente a formato SEO-friendly.
    
    Args:
        file_path: Ruta completa del archivo
    
    Returns:
        Nueva ruta del archivo renombrado
        
    Raises:
        FileNotFoundError: Si el archivo no existe
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"El archivo no existe: {file_path}")
    
    # Obtener directorio y nombre
    directory = path.parent
    filename = path.name
    
    # Slugificar nombre
    new_filename = slugify_filename(filename)
    
    # Si el nombre es el mismo, no hacer nada
    if new_filename == filename:
        return file_path
    
    # Crear nueva ruta
    new_path = directory / new_filename
    
    # Si ya existe un archivo con ese nombre, agregar UUID
    if new_path.exists():
        name, ext = os.path.splitext(new_filename)
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"{name}-{unique_id}{ext}"
        new_path = directory / new_filename
    
    # Renombrar archivo
    path.rename(new_path)
    
    return str(new_path)
