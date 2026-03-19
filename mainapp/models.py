from django.db import models
from django.contrib.auth.models import User


# ----------------------
# Category Model
# ----------------------
class Category(models.Model):
    name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


# ----------------------
# Worker Model
# ----------------------
class Worker(models.Model):
    AREA_CHOICES = [
        ('Kothrud', 'Kothrud'),
        ('Baner', 'Baner'),
        ('Wakad', 'Wakad'),
        ('Hinjewadi', 'Hinjewadi'),
        ('Hadapsar', 'Hadapsar'),
        ('Shivajinagar', 'Shivajinagar'),
        ('NDARoad', 'NDA Road'),
        ('Uttamnagar', 'Uttamnagar'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    experience = models.IntegerField()
    address = models.TextField()

    area = models.CharField(
        max_length=50,
        choices=AREA_CHOICES,
        default='Kothrud'
    )

    profile_image = models.ImageField(upload_to='workers/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    max_jobs_per_day = models.IntegerField(default=3)

    def __str__(self):
        return self.user.username


# ----------------------
# Booking Model
# ----------------------
class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Finished', 'Finished'),
        ('Cancelled', 'Cancelled'),
    ]

    TIME_SLOT_CHOICES = [
        ('Morning', 'Morning (8AM - 12PM)'),
        ('Afternoon', 'Afternoon (12PM - 4PM)'),
        ('Evening', 'Evening (4PM - 8PM)'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_bookings')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    service_date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOT_CHOICES, default='Morning')
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Booking {self.id} - {self.customer.username} - {self.worker.user.username}"


# ----------------------
# Payment Model
# ----------------------
class Payment(models.Model):
    PAYMENT_METHODS = [
        ('UPI', 'UPI'),
        ('Card', 'Card'),
        ('Net Banking', 'Net Banking'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(auto_now_add=True)
    is_refunded = models.BooleanField(default=False)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Payment for Booking {self.booking.id}"


# ----------------------
# Review Model
# ----------------------
class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()

    def __str__(self):
        return f"{self.worker.user.username} - {self.rating} stars"


# ----------------------
# Customer Lead Model
# ----------------------
class CustomerLead(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    area = models.CharField(max_length=100)
    service_needed = models.CharField(max_length=100)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"