from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_item, name='upload'),
    path('register/', views.register, name='register'), 
    path('set-language/', views.set_language, name='set_language'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='pages/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('my/', views.my, name='my'),
    path('message/', views.messages_center, name='message'),
    path('messages/<str:username>/', views.chat_thread, name='chat_thread'),
    path('item/<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('item/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('item/<int:item_id>/toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('item/<int:item_id>/purchase/', views.purchase_item, name='purchase_item'),
    path('item/<int:item_id>/send_request/', views.send_purchase_request, name='send_purchase_request'),
    path('item/<int:item_id>/confirm_deal/<str:buyer_username>/', views.confirm_deal, name='confirm_deal'),
] 