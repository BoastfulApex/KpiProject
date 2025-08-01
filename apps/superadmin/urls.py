from django.urls import path
from apps.superadmin import views

urlpatterns = [

    path('filials/', views.filials, name='admin_filials'),
    path('filial_create/', views.filial_create, name='admin_filial_create'),
    path('filial/<int:pk>', views.filial_detail, name='admin_filial_update'),
    path('filial_delete/<int:pk>', views.FilialDelete.as_view(), name='admin_filial_delete'),
    path('admins/', views.admin_list, name='admin_adminstrators'),
    path('admins/create/', views.admin_create, name='admin_adminstrator_create'),
    path('admins/<int:pk>/', views.admin_detail, name='admin_adminstrator_detail'),
    path('admins/<int:pk>/delete/', views.AdminstratorDeleteView.as_view(), name='admin_adminstrator_delete'),
    path('select-filial/<str:filial_id>/', views.select_filial, name='admin_select_filial'),
   
]
