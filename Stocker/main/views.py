from django.conf import settings
from django.shortcuts import render,redirect
from django.http import HttpRequest
from . import forms,models
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q,Count, Avg
from django.core.mail import EmailMessage
from django.utils.timezone import localtime
import os
from django.contrib.auth.models import Group
from django.utils import timezone
from datetime import datetime, timedelta
import csv
from django.http import HttpResponse


def login_view(request:HttpRequest):

    if request.method == "POST":
        form = forms.LoginForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']

        if form.is_valid():
 
                user = authenticate(request, username=username, password=password)
                if user:
                    #Check products that reach expire date soon
                    managers = User.objects.filter(is_superuser=True).all()

                    products_expiring_soon = models.Product.objects.filter(
                        expire_date__lte=timezone.now().date() + timedelta(days=10),
                        expire_date__gte=timezone.now().date()
                    )

                    for product in products_expiring_soon:
                        days_until_expiry = (product.expire_date - timezone.now().date()).days
                        try:
                            content = f"""
                            <html>
                            <body>
                                <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                                    <h2 style="color: #d9534f;">⚠️ Product Expiry Alert</h2>
                                    <div style="background-color: #f9f9f9; padding: 15px; margin: 15px 0; border-left: 4px solid #d9534f;">
                                        <p><strong>Product:</strong> {product.title}</p>
                                        <p><strong>Expiry Date:</strong> {product.expire_date.strftime('%Y-%m-%d')}</p>
                                        <p><strong>Days Remaining:</strong> {days_until_expiry} days</p>
                                        <p><strong>Status:</strong> {"Expired" if days_until_expiry <= 0 else "Expiring soon"}</p>
                                    </div>
                                </div>
                            </body>
                            </html>
                            """
                            for manager in managers:
                                if manager.email:
                                    email = EmailMessage(
                                        "Product Expiry Alert",
                                        content,
                                        settings.DEFAULT_FROM_EMAIL,
                                        [manager.email],
                                    )
                                    email.content_subtype = "html"
                                    email.send()
                        except Exception as e:
                            print(e)
                    login(request, user)
                    return redirect("main:home_view")
                else: 
                    form.add_error('username', 'username or password incorrect')

    else:
        form = forms.LoginForm()

    return render(request, 'login.html', {
        "form": form,
    })

def home_view(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')

    avg_products_per_supplier = models.Supplier.objects.annotate(
        product_count=Count('product')
        ).aggregate(
            Avg('product_count')
            )['product_count__avg']
    last_30_days = timezone.localtime() - timedelta(days=30)
    new_suppliers_count = models.Supplier.objects.filter(created_at__gte=last_30_days).count()

    data = {
        "total_products": models.Product.objects.count(),
        "total_products_in_stock": models.Product.objects.filter(Q(stock__gt=100)).count(),
        "total_products_low_stock": models.Product.objects.filter(Q(stock__lt=100)).count(),
        "total_products_out_of_stock": models.Product.objects.filter(Q(stock=0)).count(),
        "products_average_prices": models.Product.objects.aggregate(Avg('price'))['price__avg'],
        "average_product_for_supplier":avg_products_per_supplier,
        "new_suppliers_count":new_suppliers_count,
        "suppliers_with_products": models.Supplier.objects.annotate(products_count=Count('product')).filter(products_count__gt=0).count(),
        "suppliers_without_products": models.Supplier.objects.annotate(products_count=Count('product')).filter(products_count=0).count(),
        "total_categories":models.Category.objects.count(),
        "total_suppliers":models.Supplier.objects.count(),
        "total_users":User.objects.filter(is_superuser=False).count()
    }
    products = models.Product.objects.order_by('stock')[:5]
    highest_suppliers = models.Supplier.objects.annotate(products_count = Count('product', distinct=False)).order_by('-products_count')[:5]
    return render(request, "home.html", {
        "data":data,
        "products":products,
        "highest_suppliers":highest_suppliers

    })


def products_view(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')

    if not request.user.has_perm('main.view_product'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    

    if "search" in request.GET:
        products = models.Product.objects.filter(title__contains=request.GET["search"])
    else:
        products = models.Product.objects.all()

    today = localtime().date()

    for product in products:
        product.days_to_expire = (product.expire_date - today).days
        
        
    paginator = Paginator(products, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "products/home.html",{
        "products": page_obj
    })





def add_product(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')

    if not request.user.has_perm('main.add_product'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
    
    if request.method == "POST":
        form = forms.ProductForm(request.POST, request.FILES)

        if form.is_valid():
            image = request.FILES.get('image', models.Product._meta.get_field('image').default)
            category = models.Category.objects.get(id=request.POST['category'])
            new_product = models.Product(
                title=request.POST['title'],
                description=request.POST['description'],
                image=image,
                price=request.POST['price'],
                expire_date=request.POST['expire_date'],
                Category=category,
            )
            new_product.save()
            new_product.suppliers.set(request.POST.getlist('suppliers')) 
            messages.success(request,"Product added sucessfully !", 'bg-green-500')
            return redirect("main:products_view")
        else:
            print("error")
     
            
        

    else:
        form = forms.SupplierForm()


    categories = models.Category.objects.all()
    suppliers = models.Supplier.objects.all()
    return render(request, "products/add_product.html", {
        "form": form,
        "categories": categories,
        "suppliers": suppliers
    })

def edit_product(request:HttpRequest, id:int):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.edit_product'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
    
    product = models.Product.objects.get(pk=id)
    if not product:
        messages.warning(request,"sorry ! the enetred product not exists", "bg-red-300")
        return redirect('main:home_view')

    
    if request.method == "POST":
        form = forms.ProductForm(request.POST)
        category = models.Category.objects.get(id=request.POST['category'])
        if form.is_valid():
            product.title = request.POST['title']
            product.description=request.POST['description']
            product.price=request.POST['price']
            product.expire_date=request.POST['expire_date']
            product.Category=category
            if request.FILES.get('image'):
                image_path = os.path.join(settings.MEDIA_ROOT, product.image.name)
                if os.path.isfile(image_path):
                    os.remove(image_path)
                product.image = request.FILES['image']
                        

            product.save()
            messages.success(request,"Product updated sucessfully !", 'bg-green-500')
            return redirect("main:products_view")
     
            
        

    else:
        form = forms.ProductForm()


    categories = models.Category.objects.all()
    suppliers = models.Supplier.objects.all()
    return render(request, "products/edit_product.html", {
        "form": form,
        "product":product,
        "categories": categories,
        "suppliers": suppliers
    })

def delete_product(request:HttpRequest, id:int):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.delete_product'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
    
    product = models.Product.objects.get(pk=id)

    if product:
        if product.image:
            image_path = os.path.join(settings.MEDIA_ROOT, product.image.name)
            if os.path.isfile(image_path):
                os.remove(image_path)
        product.delete()
        messages.success(request,"Product deleted sucessfully !", 'bg-green-500')
        return redirect("main:products_view")

def categories_view(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    

    if not request.user.has_perm('main.view_category'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
    
    if "searchcategory" in request.GET:
        categories = models.Category.objects.filter(title__contains=request.GET["searchcategory"])
    else:
        categories = models.Category.objects.all()

    paginator = Paginator(categories, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "categories/categories.html",{
        "categories": page_obj
    })


def add_category(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.add_category'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
    
    if request.method == "POST":
        form = forms.CategoryForm(request.POST)

        if form.is_valid():
            new_category = models.Category(title=request.POST['category_title'])
            new_category.save()
            messages.success(request,"category added sucessfully !", 'bg-green-500')
            return redirect("main:categories_view")
     
            
        

    else:
        form = forms.CategoryForm()


    return render(request, "categories/add_category.html", {
        "form": form,
    })


def edit_category(request:HttpRequest, id:int):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.change_category'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
    
    category = models.Category.objects.get(pk=id)
    if not category:
        messages.warning(request,"sorry ! the enetred category not exists", "bg-red-300")
        return redirect('main:home_view')

    
    if request.method == "POST":
        form = forms.CategoryForm(request.POST)

        if form.is_valid():
            category.title = request.POST['category_title']
            category.save()
            messages.success(request,"category updated sucessfully !", 'bg-green-500')
            return redirect("main:categories_view")
     
            
        

    else:
        form = forms.CategoryForm()


    return render(request, "categories/edit_category.html", {
        "form": form,
        "category":category
    })

def delete_category(request:HttpRequest, id:int):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.delete_category'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
    
    category = models.Category.objects.get(pk=id)

    if category:
        category.delete()
        messages.success(request,"category deleted sucessfully !", 'bg-green-500')
        return redirect("main:categories_view")


def suppliers_view(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.view_supplier'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')       
    
    if "searchsupplier" in request.GET:
        suppliers = models.Supplier.objects.filter(name__contains=request.GET["searchsupplier"])
    else:
        suppliers = models.Supplier.objects.all()

    paginator = Paginator(suppliers, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "suppliers/home.html",{
        "suppliers": page_obj
    })


def add_supplier(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.add_supplier'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
    
    if request.method == "POST":
        form = forms.SupplierForm(request.POST, request.FILES)

        if form.is_valid():
            logo = request.FILES.get('logo', models.Supplier._meta.get_field('logo').default)
            new_supplier = models.Supplier(
                name=request.POST['name'],
                logo=logo,
                email=request.POST['email'],
                website=request.POST['website'],
                phone=request.POST['phone']
            )
            new_supplier.save()
            messages.success(request,"Supplier added sucessfully !", 'bg-green-500')
            return redirect("main:suppliers_view")
     
            
        

    else:
        form = forms.SupplierForm()



    return render(request, "suppliers/add_supplier.html", {
        "form": form,
    })


def edit_supplier(request:HttpRequest, id:int):
    print(request.user.get_all_permissions())
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.change_supplier'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
    
    supplier = models.Supplier.objects.get(pk=id)
    if not supplier:
        messages.warning(request,"sorry ! the enetred supplier not exists", "bg-red-300")
        return redirect('main:home_view')

    
    if request.method == "POST":
        form = forms.SupplierForm(request.POST)

        if form.is_valid():
            supplier.name = request.POST['name']
            if request.FILES.get('logo'):
                image_path = os.path.join(settings.MEDIA_ROOT, supplier.logo.name)
                if os.path.isfile(image_path):
                    os.remove(image_path)
                supplier.logo = request.FILES['logo']
                        
            supplier.email = request.POST['email']
            supplier.website = request.POST['website']
            supplier.phone = request.POST['phone']
            supplier.save()
            messages.success(request,"Supplier updated sucessfully !", 'bg-green-500')
            return redirect("main:suppliers_view")
     
            
        

    else:
        form = forms.SupplierForm()


    return render(request, "suppliers/edit_supplier.html", {
        "form": form,
        "supplier":supplier
    })

def delete_supplier(request:HttpRequest, id:int):
    supplier = models.Supplier.objects.get(pk=id)
    if not request.user.has_perm('main.delete_supplier'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    

    if supplier:
        image_path = os.path.join(settings.MEDIA_ROOT, supplier.logo.name)
        if os.path.isfile(image_path):
            os.remove(image_path)
        supplier.delete()
        messages.success(request,"Supplier deleted sucessfully !", 'bg-green-500')
        return redirect("main:suppliers_view")
    

def users_view(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')

    if request.user.has_perm('auth.view_user'):
        if "searchuser" in request.GET:
            users = User.objects.filter(Q(first_name__contains=request.GET["searchuser"]) and Q(is_superuser=False))
        else:
            users = User.objects.filter(is_superuser=False)
    else:
        users = []
        messages.error(request,'Sorry ! you cannot access to this page !', 'bg-red-400')

    paginator = Paginator(users, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "users/home.html",{
        "users": page_obj
    })


def edit_user(request:HttpRequest, id:int):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('auth.change_user'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')       
    
    user = User.objects.get(pk=id)
    if not user:
        messages.warning(request,"sorry ! the enetred user not exists", "bg-red-300")
        return redirect('main:home_view')

    
    if request.method == "POST":
        form = forms.EditUserForm(request.POST)

        if form.is_valid():
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.username = request.POST['username']
            user.email = request.POST['email']
            user.save()
            messages.success(request,"User updated sucessfully !", 'bg-green-500')
            return redirect("main:users_view")
     
            
        

    else:
        form = forms.EditUserForm()

    groups = Group.objects.all()
    return render(request, "users/edit_user.html", {
        "form": form,
        "user":user,
        "groups":groups
    })

def delete_user(request:HttpRequest, id:int):
    if not request.user.has_perm('auth.delete_user'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')    
       
    user = User.objects.get(pk=id)

    if user:
        user.delete()
        messages.success(request,"User deleted sucessfully !", 'bg-green-500')
        return redirect("main:users_view")
    



def add_user(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('auth.add_user'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')       
    
    if request.method == "POST":
        print(request.POST)
        form = forms.UserForm(request.POST, request.FILES)

        if request.POST['password'] != request.POST['confirm_password']:
            form.add_error('password', 'passwords not equals')
        group = Group.objects.get(pk=request.POST['group'])
        if form.is_valid():
            new_user = User.objects.create_user(
            first_name = request.POST['first_name'],
            last_name = request.POST['last_name'],
            username = request.POST['username'],
            email = request.POST['email'],
            password=request.POST['password'],
            )
            new_user.save()
            new_user.groups.add(group)
            messages.success(request,"User added sucessfully !", 'bg-green-500')
            return redirect("main:users_view")
     
            
        

    else:
        form = forms.UserForm()


    groups = Group.objects.all()
    return render(request, "users/add_user.html", {
        "form": form,
        "groups": groups
    })





def supplier_products_view(request:HttpRequest,id:int):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.view_product'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')       
    
    supplier = models.Supplier.objects.get(pk=id)

    if "search" in request.GET:
        products = supplier.product_set.filter(title__contains=request.GET["search"])
    else:
        products = supplier.product_set.all()

    today = localtime().date()

    for product in products:
        product.days_to_expire = (product.expire_date - today).days
        
        
    paginator = Paginator(products, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "suppliers/supplier_products.html",{
        "products": page_obj,
        "supplier":supplier
    })



def product_suppliers_view(request:HttpRequest, id:int):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')

    if not request.user.has_perm('main.view_supplier'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')       
    
    

    product = models.Product.objects.get(pk=id)
    if "searchsupplier" in request.GET:
        suppliers = product.suppliers.filter(name__contains=request.GET["searchsupplier"])
    else:
        suppliers = product.suppliers.all()

    paginator = Paginator(suppliers, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "suppliers/home.html",{
        "suppliers": page_obj
    })


def update_product_stock(request:HttpRequest, id:int):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')

    if not request.user.has_perm('main.update_stock'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')     
    
    product = models.Product.objects.get(pk=id)
    if not product:
        messages.warning(request,"sorry ! the enetred product not exists", "bg-red-300")
        return redirect('main:home_view')

    
    if request.method == "POST":
            product.stock=request.POST['stock']
            product.save()

            # check stock to send email
            managers = User.objects.filter(is_superuser=True).all()
            if int(product.stock) <= 100:
                try:
                    content = f"""
                    <html>
                    <body>
                        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                            <h2 style="color: #d9534f;">⚠️ Low Stock Alert</h2>
                            <div style="background-color: #f9f9f9; padding: 15px; margin: 15px 0; border-left: 4px solid #d9534f;">
                                <p><strong>Product:</strong> {product.title}</p>
                                <p><strong>Current Stock:</strong> {product.stock} units</p>
                                <p><strong>Date:</strong> {product.created_at.strftime('%Y-%m-%d')}</p>
                                <p><strong>Status:</strong> reach minimum Stock (100 units)</p>
                            </div>
                            <p>Thank you
                        </div>
                    </body>
                    </html>
                    """
                    for manager in managers:
                        if manager.email:
                            email = EmailMessage(
                            "Low Stock Alert",
                                content,
                                settings.DEFAULT_FROM_EMAIL,
                                [manager.email],
                            )
                            email.content_subtype = "html"
                            email.send()
                except Exception as e:
                    print(e)


            messages.success(request,"Product stock updated sucessfully !", 'bg-green-500')
            return redirect("main:products_view")
     

    return render(request, "products/update_stock.html", {
        "product":product,
    })


def logout_view(request:HttpRequest):
    logout(request)
    return redirect('main:login_view')


def export_products(request:HttpRequest):
    
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.view_product'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="products.csv"'},
    )
    
    writer = csv.writer(response)
    
    writer.writerow(['ID', 'Title', 'Description', 'Price', 'Stock', 'Expire Date', 'Category', '#Suppliers'])
    
    products = models.Product.objects.all()
    
    for product in products:
        suppliers = product.suppliers.count()
        writer.writerow([
            product.id,
            product.title,
            product.description,
            product.price,
            product.stock,
            product.expire_date.strftime('%Y-%m-%d'),
            product.Category.title,
            suppliers
        ])
    
    return response

def import_csv(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
    if not request.user.has_perm('main.add_product'):
        messages.warning(request,"sorry ! you cannot access to previous page", "bg-orange-300")
        return redirect('main:home_view')
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "This file is not a CSV file", "bg-red-500")
            return redirect('main:import_csv')
        
        try:
            file_data = csv_file.read().decode('utf-8')
            csv_data = csv.reader(file_data.splitlines())
            
            next(csv_data, None)
            
            products_added = 0
            for row in csv_data:
                if len(row) >= 6: 
                    title = row[1]
                    description = row[2]
                    price = float(row[3])
                    stock = int(row[4])
                    expire_date = row[5]
                    category_name = row[6]

                    expire_date = datetime.strptime(row[5], "%Y-%m-%d").date()
                
                    category = models.Category.objects.filter(title=category_name).first()
                    if not category:
                        category = models.Category(title=category_name)
                        category.save()

                    product = models.Product(
                        title=title,
                        description=description,
                        price=price,
                        stock=stock,
                        expire_date=expire_date,
                        Category=category
                    )
                    product.save()
                    products_added += 1
                    
            messages.success(request, f"{products_added} products imported successfully!", "bg-green-500")
            return redirect('main:products_view')
            
        except Exception as e:
            messages.error(request, f"Error importing CSV: {str(e)}", "bg-red-500")
    
    return render(request, "import_csv.html")