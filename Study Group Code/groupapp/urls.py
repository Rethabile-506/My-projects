
from django.urls import path, include
from django.views.generic import TemplateView
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('group_list', views.groups, name='group_list'),
    path('group_detail/<int:pk>',
         views.group_detail, name='group_detail'),
    path('add_post/<int:pk>', views.add_post, name='add_post'),
    path('profile_detail/<int:pk>', views.profile_detail, name='profile_detail'),
    path('join/<int:pk>', views.join, name='join'),
    path('leave/<int:pk>', views.leave, name='leave'),
    path('cat_list/<int:pk>', views.cat_list, name='cat_list'),
]
