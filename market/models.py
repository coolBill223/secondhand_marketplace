from django.db import models
from django.contrib.auth.models import User

class Item(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    is_sold = models.BooleanField(default=False)
    favorited_by = models.ManyToManyField(User, related_name='favorites', blank=True)

    # New fields
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('slightly_used', 'Slightly Used'),
        ('used', 'Used'),
        ('dysfunctional', 'Dysfunctional'),
    ]
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')

    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('textbooks', 'Textbooks'),
        ('furniture', 'Furniture'),
        ('school_supplies', 'School supplies'),
        ('clothing', 'Clothing'),
        ('housing', 'Housing'),
        ('pet_supplies', 'Pet Supplies'),
        ('misc', 'Miscellaneous'),
    ]
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='misc')

    pickup = models.BooleanField(default=False)
    delivery = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='items/')

    def __str__(self):
        return f"{self.item.title} - Image"

class Order(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.username} bought {self.item.title}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL)
    decision = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}"
