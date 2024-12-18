from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now


# Create your models here.

class User(models.Model):
    """
    Represents a user in the system. Each user can have a specific role, such as client or therapist.
    """

    ROLE_CHOICES = [
        ('client', 'مراجع'),
        ('therapist', 'مشاور'),
        ('center', 'مرکز'),
        ('owner', 'ادمین اصلی'),
    ]

    phone_number = models.CharField(max_length=11, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role} - {self.phone_number}"

class Client(models.Model):
    """
    Represents a client profile, linked to a user account.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    fullname = models.CharField(max_length=255, blank=True)
    profile_image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.fullname

class Therapist(models.Model):
    """
    Represents a therapist profile, linked to a user account.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='therapist_profile')
    center = models.ForeignKey('Center', on_delete=models.CASCADE, related_name='therapists')
    fullname = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField()

    def __str__(self):
        return self.fullname


class Center(models.Model):
    """
    Represents a therapy or medical center where therapists work.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='center_profile')
    name = models.CharField(max_length=255)
    address = models.TextField()
    open_time = models.TimeField()
    close_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile')
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.user.phone_number} {self.name}'

class OneTimePassword(models.Model):
    value = models.TextField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    expire_time = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return now() > self.expire_time