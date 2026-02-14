from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    group = models.ManyToManyField("Group")
    user_profile = models.ImageField(
        upload_to="user_profile", default="default.jpg")
    about = models.CharField(max_length=250)

    def __str__(self):
        return self.user.username

class Category(models.Model):
    category = models.CharField(max_length=100)

    def __str__(self):
        return self.category


class Group(models.Model):
    name = models.CharField(max_length=15)
    group_profile = models.ImageField(
        upload_to="group_profile", default="default.jpg")
    category = models.ManyToManyField(Category)

    def __str__(self):
        return self.name



class Post(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    title = models.CharField(max_length=400)
    user_file = models.FileField(upload_to='documents', blank=True, null=True)
    description = models.CharField(max_length=10000, null=True, blank=True)
    picture = models.ImageField(
        null=True, blank=True, upload_to='news_images')

    def __str__(self):
        return self.title
