from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number=None, email=None, password=None, **extra_fields):
        if not phone_number and not email:
            raise ValueError('The Phone Number or Email field must be set')

        if phone_number:
            if CustomUser.objects.filter(phone_number=phone_number).exists():
                raise ValueError('A user with this phone number already exists.')

        if email:
            email = self.normalize_email(email)
            if CustomUser.objects.filter(email=email).exists():
                raise ValueError('A user with this email already exists.')

        # Create user with provided fields
        user = self.model(phone_number=phone_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number=None, email=None, password=None, **extra_fields):
        if email is None:
            raise ValueError('Superusers must have an email address.')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number=phone_number, email=email, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Added balance field
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Height in meters
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # Weight in kilograms
    bmi = models.FloatField(null=True, blank=True)  # BMI
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email if self.email else self.phone_number

    def save(self, *args, **kwargs):
        # Calculate BMI before saving
        if self.height and self.weight:
            height_in_meters = self.height / 100
            self.bmi = round(self.weight / (height_in_meters ** 2), 2)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_transactions', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_transactions',
                                  on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Transaction of {self.amount} from {self.sender} to {self.recipient} on {self.date}'


class Notification(models.Model):
    title = models.CharField(max_length=100, default="No Title")
    message = models.TextField(default="No Message")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class TopUpRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def user_first_name(self):
        return self.user.first_name

    def __str__(self):
        return f"TopUpRequest(user={self.user_first_name}, amount={self.amount}, is_approved={self.is_approved}, created_at={self.created_at})"

# Food System
class Canteen(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class FoodCategory(models.Model):
    name = models.CharField(max_length=100)
    canteen = models.ForeignKey(Canteen, related_name='categories', on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f"{self.name} - {self.canteen.name}"

class Food(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(FoodCategory, related_name='foods', on_delete=models.CASCADE, default=1)
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vendor_foods', on_delete=models.CASCADE, null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_approved:
            FeaturedFood.objects.get_or_create(food=self)
        else:
            FeaturedFood.objects.filter(food=self).delete()

    def __str__(self):
        return self.name

class FeaturedFood(models.Model):
    food = models.OneToOneField(Food, on_delete=models.CASCADE, related_name='featured')

    def __str__(self):
        return f"Featured: {self.food.name}"

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    food = models.ForeignKey(Food, related_name='orders', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    vendor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='vendor_orders', on_delete=models.CASCADE, null=True, blank=True)
    is_paid = models.BooleanField(default=False)  # Add this line

    def __str__(self):
        return f"Order by {self.user} for {self.quantity}x {self.food.name}"