from django.contrib import admin

# Register your models here.
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio', 'stock', 'necesita_reposicion']
    list_filter = ['stock']
    search_fields = ['nombre']