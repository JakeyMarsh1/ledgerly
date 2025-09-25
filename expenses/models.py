from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    INCOME = 'INCOME'
    OUTGO = 'OUTGO'
    TYPE_CHOICES = [
        (INCOME, 'Income'),
        (OUTGO, 'Outgoing'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=6, choices=TYPE_CHOICES)
    amount_in_cents = models.IntegerField()
    occurred_on = models.DateField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type}: {self.amount_in_cents} ({self.occurred_on})"