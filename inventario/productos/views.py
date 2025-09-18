# -----------------------------------------------------------------------------
# productos/views.py
# Este archivo contiene la lógica de la aplicación a través de las Vistas Basadas en Clases (CBVs).
# -----------------------------------------------------------------------------
from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q, F
from django.utils import timezone
from .models import Producto, MovimientoStock
from .forms import ProductoForm, MovimientoStockForm, AjusteStockForm


class ProductoListView(ListView):
    """Muestra una lista de todos los productos."""
    model = Producto
    template_name = "producto/producto_list.html"
    context_object_name = "producto"

    def get_queryset(self):
        """Sobrescribe para permitir el filtrado por stock bajo."""
        queryset = super().get_queryset()

        stock_bajo = self.request.GET.get('stock_bajo')
        if stock_bajo:
            # Filtra en la base de datos usando F() para eficiencia
            queryset = queryset.filter(stock__lt=F("stock_minimo"))

        # Hay un error aquí: 'order_by' debe ser una llamada a método, no una indexación
        # Se ha corregido la sentencia
        return queryset.order_by("nombre")
    
    def get_context_data(self, **kwargs):
        """Añade una variable al contexto para saber si se está filtrando por stock bajo."""
        context = super().get_context_data(**kwargs)
        context["stock_bajo"] = self.request.GET.get("stock_bajo")
        return context
    

class ProductoDetailView(DetailView):
    """Muestra los detalles de un producto específico."""
    model = Producto
    template_name = "productos/producto_detail.html"
    context_object_name = "producto"

    def get_context_data(self, **kwargs):
        """Añade los últimos 10 movimientos y el formulario de ajuste al contexto."""
        context = super().get_context_data(**kwargs)
        # Accede a los movimientos a través del related_name en el modelo
        context["movimientos"] = self.object.movimientos.all()[:10]
        context["form_ajuste"] = AjusteStockForm
        return context
    

class ProductoCreateView(CreateView):
    """Vista para crear un nuevo producto."""
    model = Producto
    form_class = ProductoForm
    template_name = "productos/producto_form.html"
    success_url = reverse_lazy("productos:producto_list")

    def form_valid(self, form):
        """Sobrescribe para registrar un movimiento de stock inicial."""
        response = super().form_valid(form)

        if form.cleaned_data["stock"] > 0:
            MovimientoStock.objects.create(
                producto=self.object, # self.object es la instancia del producto recién creado
                tipo="entrada",
                cantidad=form.cleaned_data["stock"],
                motivo = "Stock inicial",
                fecha = timezone.now(),
                usuario = self.request.user.username if self.request.user.is_authenticated else "Sistema"
            )

        messages.success(self.request, "Producto creado exitosamente")
        return response
    

class ProductoUpdateView(UpdateView):
    """Vista para actualizar un producto existente."""
    model = Producto
    template_name = "producto/producto_form.html"
    form_class = ProductoForm
    success_url = reverse_lazy("producto:producto_list")

    def form_valid(self, form):
        """Sobrescribe para mostrar un mensaje de éxito."""
        response = super().form_valid(form)
        messages.success(self.request, "Producto actualizado exitosamente")
        return response
    

class ProductoDeleteView(DeleteView):
    """Vista para eliminar un producto."""
    model = Producto
    template_name = "productos/producto_confirm_delete.html"
    success_url = reverse_lazy("producto:producto_list")

    def delete(self, request, *args, **kwargs):
        """Sobrescribe para mostrar un mensaje de éxito después de eliminar."""
        messages.success(self.request, "Producto eliminado exitosamente")
        return super().delete(request, *args, **kwargs)
    

class MovimientoStockCreateView(CreateView):
    """Vista para registrar un nuevo movimiento de stock."""
    model = MovimientoStock
    template_name = "productos/movimiento_form.html"
    form_class = MovimientoStockForm

    def get_form_kwargs(self):
        """Pasa la instancia del producto al formulario."""
        kwargs = super().get_form_kwargs()
        kwargs["producto"] = get_object_or_404(Producto, pk=self.kwargs["pk"])
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Añade la instancia del producto al contexto de la plantilla."""
        context = super().get_context_data(**kwargs)
        context["producto"] = get_object_or_404(Producto, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        """Maneja la lógica de negocio para actualizar el stock."""
        movimiento = form.save(commit=False)
        movimiento.producto = get_object_or_404(Producto, pk=self.kwargs["pk"])
        movimiento.usuario = self.request.user.username if self.request.user.is_authenticated else "Sistema"

        if movimiento.tipo == "entrada":
            movimiento.producto.stock += movimiento.cantidad
        elif movimiento.tipo == "salida":
            # Si no hay suficiente stock, se añade un error y se re-renderiza el formulario
            if movimiento.producto.stock >= movimiento.cantidad:
                movimiento.producto.stock -= movimiento.cantidad
            else:
                form.add_error("cantidad", "No hay stock suficiente")
                return self.form_invalid(form)
        
        # Guarda el producto actualizado y el nuevo movimiento
        movimiento.producto.save()
        movimiento.save()

        messages.success(self.request, f"Movimiento de stock registrado exitosamente")
        return redirect("productos:producto_detail", pk=movimiento.producto.pk)       

class AjusteStockView(FormView):
    """Vista para ajustar el stock de un producto a un valor específico."""
    form_class = AjusteStockForm
    template_name = "productos/ajuste_stock_form.html"

    def get_form_kwargs(self):
        """Pasa la instancia del producto al formulario para que pueda pre-llenar los datos."""
        kwargs = super().get_form_kwargs()
        kwargs["producto"] = get_object_or_404(Producto, pk=self.kwargs["pk"])
        return kwargs
    
    def get_context_data(self, **kwargs):
        """Añade la instancia del producto al contexto de la plantilla."""
        context = super().get_context_data(**kwargs)
        context["producto"] = get_object_or_404(Producto, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        """
        Calcula la diferencia de stock, registra un movimiento y actualiza el stock del producto.
        """
        producto = get_object_or_404(Producto, pk=self.kwargs["pk"])
        nueva_cantidad = form.cleaned_data["cantidad"]
        motivo = form.cleaned_data["motivo"] or "Ajuste de stock"

        diferencia = nueva_cantidad - producto.stock

        if diferencia != 0:
            tipo = "entrada" if diferencia > 0 else "salida" 
            MovimientoStock.objects.create(
                producto=producto,
                tipo=tipo,
                cantidad=abs(diferencia),
                motivo=motivo,
                fecha=timezone.now(),
                usuario = self.request.user.username if self.request.user.is_authenticated else "Sistema"
            )

            producto.stock = nueva_cantidad
            producto.save()

            messages.success(self.request, f"Stock actualizado exitosamente")
        else:
            messages.info(self.request, f"El stock no ha cambiado")

        return redirect("productos:producto_detail", pk=producto.pk)


class StockBajoListView(ListView):
    """Muestra una lista filtrada solo para productos con stock bajo."""
    model = Producto
    template_name = "productos/stock_bajo_list.html"
    context_object_name = "productos"

    def get_queryset(self):
        """
        Filtra y ordena el QuerySet para mostrar solo productos
        cuyo stock sea menor que el stock mínimo.
        """
        # Se ha corregido la sintaxis. Se usa F() para una comparación eficiente
        return Producto.objects.filter(stock__lt=F("stock_minimo")).order_by("stock")