from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.ProductoListView.as_view(), name='producto_list'),
    path('nuevo/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('<int:pk>/', views.ProductoDetailView.as_view(), name='producto_detail'),
    path('<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto_update'),
    path('<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto_delete'),
    path('<int:pk>/movimiento/', views.MovimientoStockCreateView.as_view(), name='movimiento_create'),
    path('<int:pk>/ajustar-stock/', views.AjusteStockView.as_view(), name='ajustar_stock'),
    path('stock-bajo/', views.StockBajoListView.as_view(), name='stock_bajo_list'),
]