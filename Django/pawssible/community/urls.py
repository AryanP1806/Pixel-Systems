from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.community_feed, name='feed'),
    path('post/', views.create_post, name='post'),
    path('comment/<int:post_id>/', views.add_comment, name='comment'),
]
