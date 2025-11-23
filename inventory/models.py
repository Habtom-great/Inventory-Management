from django.db import models

   
class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30, unique=True)
    quantity = models.IntegerField(default=1)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
	    return self.name
# inventory/models.py

from django.db import models

class Purchase(models.Model):
    item = models.CharField(max_length=100)
    quantity = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    # Add other fields you need

class Sale(models.Model):
    item = models.CharField(max_length=100)
    quantity = models.IntegerField()
    date = models.DateField(auto_now_add=True)
    # Add other fields you need
