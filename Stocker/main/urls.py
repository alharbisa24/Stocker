from django.urls import path,include
from . import views

app_name= 'main'


urlpatterns = [
    path('login/', views.login_view, name="login_view"),
    path('', views.home_view, name="home_view"),
    path('logout/', views.logout_view, name="logout_view"),
    path('products/', views.products_view, name="products_view"),
    path('products/add', views.add_product, name="add_product"),
    path('products/<id>/edit', views.edit_product, name="edit_product"),
    path('products/<id>/update_product_stock', views.update_product_stock, name="update_product_stock"),
    path('products/<id>/delete', views.delete_product, name="delete_product"),
    path('products/<id>/suppliers', views.product_suppliers_view, name="product_suppliers_view"),
    path('products/export', views.export_products, name="export_products"),
    path('categories/', views.categories_view, name="categories_view"),
    path('categories/add', views.add_category, name="add_category"),
    path('categories/<id>/edit', views.edit_category, name="edit_category"),
    path('categories/<id>/delete', views.delete_category, name="delete_category"),
    path('suppliers/', views.suppliers_view, name="suppliers_view",),
    path('suppliers/add', views.add_supplier, name="add_supplier"),
    path('suppliers/<id>/edit', views.edit_supplier, name="edit_supplier"),
    path('suppliers/<id>/delete', views.delete_supplier, name="delete_supplier"),
    path('suppliers/<id>/products', views.supplier_products_view , name="supplier_products_view"),
    path('users/', views.users_view, name="users_view"),
    path('users/add', views.add_user, name="add_user"),
    path('users/<id>/edit', views.edit_user, name="edit_user"),
    path('users/<id>/delete', views.delete_user, name="delete_user"),
]