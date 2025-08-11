from django.conf import settings
from django.shortcuts import render,redirect
from django.http import HttpRequest
from . import forms,models
from django.contrib.auth import authenticate,login,logout
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q,Count
from django.utils.timezone import localtime
import os
from django.contrib.auth.models import Group

def login_view(request:HttpRequest):

    if request.method == "POST":
        form = forms.LoginForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']

        if form.is_valid():
 
                user = authenticate(request, username=username, password=password)
                if user:
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

    data = {
        "total_products": models.Product.objects.count(),
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
                stock=request.POST['stock'],
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
            product.stock=request.POST['stock']
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
    category = models.Category.objects.get(pk=id)

    if category:
        category.delete()
        messages.success(request,"category deleted sucessfully !", 'bg-green-500')
        return redirect("main:categories_view")


def suppliers_view(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    

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
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
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


    if "searchuser" in request.GET:
        users = User.objects.filter(Q(first_name__contains=request.GET["searchuser"]) and Q(is_superuser=False))
    else:
        users = User.objects.filter(is_superuser=False)

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
    user = User.objects.get(pk=id)

    if user:
        user.delete()
        messages.success(request,"User deleted sucessfully !", 'bg-green-500')
        return redirect("main:users_view")
    



def add_user(request:HttpRequest):
    if not request.user.is_authenticated:
        messages.warning(request,"sorry ! you must be logged in to access page", "bg-orange-300")
        return redirect('main:login_view')
    
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
