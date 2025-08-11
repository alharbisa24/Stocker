from django.db import models



class Category(models.Model):
    title= models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)




class Supplier(models.Model):
    name=models.CharField(max_length=100)
    logo = models.ImageField(upload_to="logos/",default='logos/default.jpg')
    email= models.CharField(max_length=100)
    website = models.URLField()
    phone = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)



class Product(models.Model):
    title=models.CharField(max_length=100)
    description= models.TextField()
    image = models.ImageField(upload_to="images/",default='images/default.jpg')
    price = models.CharField(max_length=20, default="0")
    stock = models.IntegerField(default=0)
    Category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="product_category")
    suppliers = models.ManyToManyField(Supplier)
    expire_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        permissions = [
            ('can_view_stock','can view stock'),
            ('can_update_stock','can_update_stock'),
            
        ]


    
