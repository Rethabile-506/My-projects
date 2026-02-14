from django import forms
from django.contrib.auth.models import User
from .models import *
from django.contrib.auth.forms import UserCreationForm


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username',
                  'password1', 'password2']




class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['user_profile', 'about']


class PostCommentForm(forms.ModelForm):
    class Meta:
        model = Post
        labels = {'title': ''}
        fields = ['title']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'description', 'user_file', 'picture']
