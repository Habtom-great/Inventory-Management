from django.urls import path

from . import views

urlpatterns = [
    path('dashboard/', views.inventory_dashboard, name='inventory_dashboard'),
    path('inventory_report/', views.inventory_report, name='inventory_report'),
    path('', views.StockListView.as_view(), name='inventory'),
    path('new', views.StockCreateView.as_view(), name='new-stock'),
    path('add-stock/', views.add_stock, name='add_stock'),
    path('stock/<pk>/edit', views.StockUpdateView.as_view(), name='edit-stock'),
    path('stock/<pk>/delete', views.StockDeleteView.as_view(), name='delete-stock'),
]