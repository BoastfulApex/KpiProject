from django.urls import path
from apps.home import views

urlpatterns = [

    path('', views.index, name='home'),
    # path('administrators/', views.admins, name='admins'),
    # path('administrators_create/', views.admin_create, name='administrators_create'),
    # path('administrators/<int:pk>', views.admin_detail, name='admin_update'),
    # path('admin_delete/<int:pk>', views.AdminDelete.as_view(), name='admin_delete'),
    path('employees/', views.employees, name='employees'),
    path('employees_create/', views.employee_create, name='employees_create'),
    path('employees/<int:pk>', views.employee_detail, name='employee_update'),
    path('employee_delete/<int:pk>', views.EmployeeDelete.as_view(), name='employee_delete'),
    path('employees/<int:employee_id>/create-schedule/', views.create_schedule_for_employee, name='create_schedule_for_employee'),

    
    # path('users/', views.users_view, name='users'),
    # path('categories/', views.categories, name='home_categories'),
    # path('categories/<int:pk>', views.category_detail, name='category_update'),
    # path('subcategories/', views.sub_categories, name='home_subcategories'),
    # path('subcategories/<int:pk>', views.subcategory_detail, name='subcategory_update'),
    # path('manufacturers/', views.manufacturers, name='home_manufacturers'),
    # path('manufacturers/<int:pk>', views.manufacturer_detail, name='manufacturer_update'),
    # path('cashback/<int:pk>', views.cashback_detail, name='cashback_update'),
    # path('products/', views.products, name='home_products'),
    # path('products/<int:pk>', views.product_detail, name='product_update'),
    # path('cashbacks_by_cashback/<int:pk>', views.user_cashback_by_cashback, name='cashbacks_by_cashback'),
    # path('notifications/', views.notifications_list, name='home_notifications'),
    # path('notification_create/', views.notification_create, name='notifications_create'),
    # path('notification/<int:pk>/', views.notification_detail, name='notifications_detail'),
    # path('notification_delete/<int:pk>/', views.NotificationDelete.as_view(), name='notifications_delete'),
    # path('sales/', views.sales, name='home_sales'),
    # path('sales_create/', views.sale_create, name='sale_create'),
    # path('sales_detail/<int:pk>', views.sale_detail, name='sale_detail'),
    # path('sales_delete/<int:pk>', views.SaleDelete.as_view(), name='sale_delete'),
    # path('story_categories/', views.story_categories, name='home_story_category'),
    # path('story_category_create/', views.story_category_create, name='story_category_create'),
    # path('story_category_delete/<int:pk>', views.StoryCategoryDelete.as_view(), name='story_category_delete'),
    # path('stories/', views.stories, name='home_stories'),
    # path('story_delete/<int:pk>', views.StoryDelete.as_view(), name='story_delete'),
    # path('story_create/', views.story_create, name='story_create'),

]
