from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='created_by', blank=True, null=True)

    def __str__(self):
        return self.user.username
