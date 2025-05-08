from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import (
    Categoria, 
    Marca, 
    Etiqueta, 
    Producto, 
    ImagenProducto, 
    AtributoProducto,
    ValorAtributoProducto,
    Inventario,
    MovimientoInventario,
    MovimientoStock
)

class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1

class ValorAtributoProductoInline(admin.TabularInline):
    model = ValorAtributoProducto
    extra = 1

@admin.register(Categoria)
class CategoriaAdmin(MPTTModelAdmin):
    list_display = ('nombre', 'slug', 'activo', 'parent')
    list_filter = ('activo', 'created_at')
    search_fields = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug', 'activo')
    list_filter = ('activo', 'created_at')
    search_fields = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    search_fields = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'marca', 'precio_venta', 'stock_actual', 'activo')
    list_filter = ('activo', 'destacado', 'categoria', 'marca')
    search_fields = ('codigo', 'nombre', 'descripcion')
    prepopulated_fields = {'slug': ('nombre',)}
    filter_horizontal = ('etiquetas',)
    inlines = [ImagenProductoInline, ValorAtributoProductoInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'slug', 'descripcion')
        }),
        ('Categorización', {
            'fields': ('categoria', 'marca', 'etiquetas')
        }),
        ('Precios y Stock', {
            'fields': ('precio_base', 'precio_venta', 'stock_actual', 'stock_minimo', 'stock_maximo')
        }),
        ('Estado', {
            'fields': ('activo', 'destacado')
        }),
    )

@admin.register(AtributoProducto)
class AtributoProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo')
    list_filter = ('tipo',)
    search_fields = ('nombre',)

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'sucursal', 'stock_actual', 'stock_minimo')
    list_filter = ('sucursal',)
    search_fields = ('producto__nombre', 'sucursal__nombre')

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('inventario', 'tipo', 'cantidad', 'usuario', 'created_at')
    list_filter = ('tipo', 'created_at')
    search_fields = ('inventario__producto__nombre', 'motivo')
    readonly_fields = ('created_at',)

@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'fecha', 'usuario')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre', 'motivo')
    readonly_fields = ('fecha',) 