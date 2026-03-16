from django.urls import path
from .views import RegisterView, LoginView, UserProfileView, UploadPhotoView, AllUsersView, UpdateUserView, DeleteUserView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('upload-photo/', UploadPhotoView.as_view(), name='upload-photo'),
    path('all/', AllUsersView.as_view(), name='all-users'),
    path('<str:uid>/update/', UpdateUserView.as_view(), name='update-user'),
    path('<str:uid>/delete/', DeleteUserView.as_view(), name='delete-user'),
]
