from django import forms
from . import models
from django.contrib.auth.models import Group

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, error_messages= {
        'required':"username is required"
    })
    password = forms.CharField(
        widget=forms.PasswordInput,
        error_messages= {
        'required':"password is required"
    }
    )


class CategoryForm(forms.Form):
    category_title = forms.CharField(max_length=100, error_messages= {
        'required':"title is required"
    })


class SupplierForm(forms.Form):
    name = forms.CharField(max_length=100, error_messages= {
        'required':"name is required"
    })
    logo = forms.ImageField(required=False)
    email = forms.EmailField(max_length=150, error_messages= {
        'required':"email is required"
    })
    website = forms.URLField(error_messages= {
        'required':"website is required"
    })
    phone = forms.CharField(error_messages= {
        'required':"phone is required"
    })
    products = forms.ModelMultipleChoiceField(
        queryset=models.Product.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        error_messages= {
        'required':"products is required"
    }
    )

class ProductForm(forms.Form):
    title = forms.CharField(max_length=100, error_messages= {
        'required':"title is required"
    })
    image = forms.ImageField(required=False)
    description = forms.CharField(max_length=500, error_messages= {
        'required':"description is required"
    })
    price = forms.CharField(max_length=100, error_messages= {
        'required':"price is required"
    })
    stock = forms.CharField(max_length=100, error_messages= {
        'required':"stock is required"
    })
    expire_date = forms.DateField(error_messages={
        'required':"expire date is required"
    })
    category = forms.ModelChoiceField(
        queryset=models.Category.objects.all(),
        empty_label="Select category",
        error_messages= {
        'required':"category is required"
    }
    )

    suppliers = forms.ModelMultipleChoiceField(
        queryset=models.Supplier.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        error_messages= {
        'required':"suppliers is required"
    }
    )



class UserForm(forms.Form):
    first_name = forms.CharField(max_length=100, error_messages= {
        'required':"first name is required"
    })
    last_name = forms.CharField(max_length=100, error_messages= {
        'required':"last name is required"
    })
    username = forms.CharField(max_length=150, error_messages= {
        'required':"username is required"
    })
    email = forms.EmailField(max_length=150, error_messages= {
        'required':"email is required"
    })
    password = forms.CharField(max_length=50, error_messages={
        'required':"password is required"
    })
    confirm_password = forms.CharField(max_length=50, error_messages={
        'required':"confirm password is required"
    })
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        empty_label="Select Group",
        error_messages= {
        'required':"Group is required"
    }
    )

class EditUserForm(forms.Form):
    first_name = forms.CharField(max_length=100, error_messages= {
        'required':"first name is required"
    })
    last_name = forms.CharField(max_length=100, error_messages= {
        'required':"last name is required"
    })
    username = forms.CharField(max_length=150, error_messages= {
        'required':"username is required"
    })
    email = forms.EmailField(max_length=150, error_messages= {
        'required':"email is required"
    })
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        empty_label="Select Group",
        error_messages= {
        'required':"Group is required"
    }
    )