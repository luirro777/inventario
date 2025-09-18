from django.db import models
import os
import uuid
from django.core.exceptions import ValidationError
from PIL import Image
from django.utils import timezone

def validate_image_size(image):
    filesize = image.file.size
    megabyte_limit = 5.0
    if filesize > megabyte_limit * 1024 * 1024:
        raise ValidationError (f"El tamaño maximo permitido es de {megabyte_limit} MB")
    
def get_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("productos", filename)

class Producto(models.Model):
    """Model definition for Producto."""

    nombre = models.CharField("Nombre", max_length=50)
    descripcion = models.CharField("Descripcion", max_length=200)
    precio = models.DecimalField("Precio", max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5, verbose_name="Stock Minimo")
    imagen = models.ImageField(
        "Imagen", 
        upload_to=get_image_path, 
        validators=[validate_image_size],
        blank=True,
        null=True,
        help_text="Formatos permitidos: jpg, png, gif. Tamaño maximo: 5MB"
    )
    fecha_creacion = models.DateTimeField("Fecha de creacion", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Fecha de creacion", auto_now=True)

    
    class Meta:
        """Meta definition for Producto."""

        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        """Unicode representation of Producto."""
        return self.nombre
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.imagen:
            try:
                img = Image.open(self.image.path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.imagen.path)
            except Exception as e:
                print(f"Error al procesar la imagen {e}")

    @property
    def necesita_reposicion(self):
        return self.stock < self.stock_minimo

class MovimientoStock(models.Model):
    """Model definition for MovimientoStock."""

    TIPO_CHOICES = [
        ("entrada", "Entrada"),
        ("salida", "Salida"),
        ("ajuste", "Ajuste"),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField("Tipo", max_length=50, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    motivo = models.CharField("Motivo", max_length=200, blank=True, null=True)
    fecha = models.DateTimeField("Fecha", default=timezone.now)
    usuario = models.CharField("Usuario", max_length=50)

    class Meta:
        """Meta definition for MovimientoStock."""

        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ["-fecha"]

    def __str__(self):
        """Unicode representation of MovimientoStock."""
        return f"{self.producto.nombre} - {self.tipo}  - {self.cantidad}" 
