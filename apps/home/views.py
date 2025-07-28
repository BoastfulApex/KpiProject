import datetime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from apps.authentication.models import *
from apps.main.forms import *
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
from django.urls import reverse
from django.shortcuts import get_object_or_404


def index(request):
    if not request.user.is_authenticated:
        return redirect('/login/')

    cashback = []
    filial = ''
    admin = None
    tashkent_time = timezone.localtime(timezone.now())
    print(tashkent_time)
    if request.user.is_superuser:
        template = 'home/superuser/super_dashboard.html'
    elif not request.user.is_superuser:
        template = 'home/user/staff_dashboard.html'
        admin = Administrator.objects.get(user=request.user)
        filial = admin.filial.filial_name
    else:
        return redirect('/login/')
    context = {
        'segment': 'dashboard',
        'cashbacks': cashback,
        "filial": filial,
        'tashkent_time': tashkent_time
    }
    
    html_template = loader.get_template(template)
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def employees(request):
    if request.user.is_superuser:
        return redirect('/login/')
    administrator = Administrator.objects.get(user=request.user)

    employees = Employee.objects.filter(filial = administrator.filial)
    search_query = request.GET.get('q')
    if search_query:
        employees = employees.filter(Q(name__icontains=search_query))
    paginator = Paginator(employees, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    tashkent_time = timezone.localtime(timezone.now())

    context = {
        'page_obj': page_obj,
        "segment": "employees",
        "filial": administrator.filial.filial_name,
        'tashkent_time': tashkent_time
    }
    html_template = loader.get_template('home/user/employees/employees.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def employee_create(request):
    if request.user.is_superuser:
        return redirect('/login/')
    administrator = Administrator.objects.get(user=request.user)
    tashkent_time = timezone.localtime(timezone.now())

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            # return redirect('employees')
            employee.filial = administrator.filial
            employee.save()          
            return redirect(reverse('create_schedule_for_employee', args=[employee.id]))    
    else:
        form = EmployeeForm()

    return render(request,
                  'home/user/employees/employee_create.html',
                  {'form': form,
                   "filial": administrator.filial.filial_name,
                   "segment": "employees",
        'tashkent_time': tashkent_time})


@login_required(login_url="/login/")
def employee_detail(request, pk):
    if request.user.is_superuser:
        return redirect('/login/')
    administrator = Administrator.objects.get(user=request.user)
    employee = Employee.objects.get(id=pk)
    tashkent_time = timezone.localtime(timezone.now())
    if employee.filial != administrator.filial:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save() 
            return redirect('employees')
    else:
        form = EmployeeForm(instance=employee)

    return render(request,
                  'home/user/employees/employee_detail.html',
                  {'form': form, 'segment': 'employees', 'employee': employee, 'tashkent_time': tashkent_time})


class EmployeeDelete(DeleteView):
    model = Employee
    fields = '__all__'
    success_url = reverse_lazy('employees')


@login_required(login_url="/login/")
def schedules(request):
    if request.user.is_superuser:
        return redirect('/login/')
    
    administrator = Administrator.objects.get(user=request.user)
    tashkent_time = timezone.localtime(timezone.now())

    all_schedules = WorkSchedule.objects.filter(employee__filial__id= administrator.filial.id)
    search_query = request.GET.get('q')
    if search_query:
        all_schedules = all_schedules.filter(Q(name__icontains=search_query))
    paginator = Paginator(all_schedules, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        "segment": "schedules",
        "filial": administrator.filial.filial_name,
        'tashkent_time': tashkent_time
    }
    html_template = loader.get_template('home/user/workschedule/schedules.html')
    return HttpResponse(html_template.render(context, request))


def create_schedule_for_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    tashkent_time = timezone.localtime(timezone.now())
    if request.method == 'POST':
        form = WorkScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.employee = employee
            schedule.save()
            form.save_m2m()  # ManyToMany uchun
            return redirect('employees')  # yoki boshqa sahifaga
    else:
        form = WorkScheduleForm()

    return render(request, 'home/user/workschedule/create_schedule_for_employee.html', 
                  {'form': form, 'employee': employee, 'tashkent_time': tashkent_time})

    
@login_required(login_url="/login/")
def create_schedule(request):
    if request.user.is_superuser:
        return redirect('/login/')
    administrator = Administrator.objects.get(user=request.user)
    tashkent_time = timezone.localtime(timezone.now())

    if request.method == 'POST':
        form = WorkScheduleWithUserForm(request.POST, admin=administrator)
        if form.is_valid():
            form.save()
            return redirect('schedules')
    else:
        form = WorkScheduleWithUserForm(admin=administrator)
    return render(request, 'home/user/workschedule/schedule_create.html', 
                  {'form': form, 
                   "filial": administrator.filial.filial_name,
                   "segment": "schedules",  'tashkent_time': tashkent_time})


class WorkScheduleDelete(DeleteView):
    model = WorkSchedule
    fields = '__all__'
    success_url = reverse_lazy('schedules')
    
# @login_required(login_url="/login/")
# def users_view(request):
#     my_queryset = MegaUser.objects.filter(is_superuser=False).all().order_by('id')
#     search_query = request.GET.get('q')
#     if search_query:
#         my_queryset = my_queryset.filter(Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query) |
#                                          Q(phone__icontains=search_query) | Q(card_code__icontains=search_query)
#                                          | Q(card_name__icontains=search_query))
#     paginator = Paginator(my_queryset, 50)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     context = {
#         'page_obj': page_obj,
#         'segment': 'users'
#     }
#     return render(request, 'home/users.html', context)


# def categories(request):
#     categories = Category.objects.all().order_by('id')
#     search_query = request.GET.get('q')
#     if search_query:
#         categories = categories.filter(Q(groupname__icontains=search_query) | Q(number__icontains=search_query))
#     paginator = Paginator(categories, 50)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     context = {
#         'page_obj': page_obj,
#         "segment": "cats"
#     }
#     html_template = loader.get_template('home/categories.html')
#     return HttpResponse(html_template.render(context, request))


# def category_detail(request, pk):
#     category = Category.objects.get(id=pk)

#     if request.method == 'POST':
#         form = CategoryForm(request.POST, request.FILES, instance=category)
#         if form.is_valid():
#             form.save()
#             return redirect('home_categories')
#     else:
#         form = CategoryForm(instance=category)

#     return render(request,
#                   'home/category_detail.html',
#                   {'form': form, 'category': category, 'segment': 'cats'})


# def sub_categories(request):
#     categories = SubCategory.objects.all().order_by('id')
#     search_query = request.GET.get('q')
#     if search_query:
#         categories = categories.filter(Q(name__icontains=search_query) | Q(code__icontains=search_query))
#     paginator = Paginator(categories, 50)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     context = {
#         'page_obj': page_obj,
#         "segment": "subcategories"
#     }
#     html_template = loader.get_template('home/subcategories.html')
#     return HttpResponse(html_template.render(context, request))


# def subcategory_detail(request, pk):
#     subcategory = SubCategory.objects.get(id=pk)

#     if request.method == 'POST':
#         form = SubCategoryForm(request.POST, request.FILES, instance=subcategory)
#         if form.is_valid():
#             form.save()
#             return redirect('home_subcategories')
#     else:
#         form = SubCategoryForm(instance=subcategory)

#     return render(request,
#                   'home/subcategory_detail.html',
#                   {'form': form, 'subcategory': subcategory, 'segment': 'subcategories'})


# def manufacturers(request):
#     categories = SubCategory.objects.all().order_by('id')
#     search_query = request.GET.get('q')
#     if search_query:
#         categories = categories.filter(Q(manufacrurer_name__icontains=search_query) | Q(code__icontains=search_query))
#     paginator = Paginator(categories, 50)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     context = {
#         'page_obj': page_obj,
#         "segment": "manufacturer"
#     }
#     html_template = loader.get_template('home/manufacturers.html')
#     return HttpResponse(html_template.render(context, request))


# def manufacturer_detail(request, pk):
#     manufacturer = Manufacturer.objects.get(id=pk)

#     if request.method == 'POST':
#         form = ManufacturerForm(request.POST, request.FILES, instance=manufacturer)
#         if form.is_valid():
#             form.save()
#             return redirect('home_manufacturers')
#     else:
#         form = ManufacturerForm(instance=manufacturer)

#     return render(request,
#                   'home/manufacturer_detail.html',
#                   {'form': form, 'subcategory': manufacturer, 'segment': 'manufacturer'})


# def products(request):
#     products = Product.objects.all().order_by('id')
#     search_query = request.GET.get('q')
#     if search_query:
#         products = products.filter(Q(itemname__icontains=search_query) | Q(itemcode__icontains=search_query))
#     paginator = Paginator(products, 50)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     context = {
#         'page_obj': page_obj,
#         "segment": "product"
#     }
#     html_template = loader.get_template('home/products.html')
#     return HttpResponse(html_template.render(context, request))


# def product_detail(request, pk):
#     product = Product.objects.get(id=pk)

#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES, instance=product)
#         if form.is_valid():
#             form.save()
#             return redirect('home_products')
#         else:
#             print("ERROR: ", form.errors)
#     else:
#         form = ProductForm(instance=product)

#     return render(request,
#                   'home/product_detail.html',
#                   {'form': form, 'product': product, 'segment': 'product'})


# def cashback_detail(request, pk):
#     cashback = Cashback.objects.get(id=pk)

#     if request.method == 'POST':
#         form = CashbackForm(request.POST, request.FILES, instance=cashback)
#         if form.is_valid():
#             form.save()
#             return redirect('home')
#     else:
#         form = CashbackForm(instance=cashback)

#     return render(request,
#                   'home/cashback_detail.html',
#                   {'form': form, 'cashback': cashback, 'segment': 'cashback'})


# def user_cashback_by_cashback(request, pk):
#     user_cashback = UserCashback.objects.filter(cashback_id=pk).all()
#     context = {
#         "cashs":user_cashback,
#         "segment":"cashback"
#     }

#     return render(request,
#                   'home/cashback_users.html', context)


# def notifications_list(request):
#     notifications = Notification.objects.all()
#     context = {
#         "notifications": notifications,
#         "segment": "notifications"
#     }

#     html_template = loader.get_template('home/notifications.html')
#     return HttpResponse(html_template.render(context, request))


# def notification_detail(request, pk):
#     notification = Notification.objects.get(id=pk)

#     if request.method == 'POST':
#         form = NotificationForm(request.POST, request.FILES, instance=notification)
#         if form.is_valid():
#             form.save()
#             return redirect('home_notifications')
#     else:
#         form = NotificationForm(instance=notification)

#     return render(request,
#                   'home/notification_update.html',
#                   {'form': form, 'notification': notification})


# def notification_create(request):
#     if request.method == 'POST':
#         form = NotificationForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('home_notifications')
#     else:
#         form = NotificationForm()

#     return render(request,
#                   'home/notification_create.html',
#                   {'form': form})


# class NotificationDelete(DeleteView):
#     model = Notification
#     fields = '__all__'
#     success_url = reverse_lazy('home_notifications')


# def sales(request):
#     sales = Sale.objects.all().order_by('id')
#     today = datetime.today().date()
#     for sale in sales:
#         if sale.expiration_date <= today:
#             sale.active = False
#             sale.save()
#     search_query = request.GET.get('q')
#     if search_query:
#         sales = sales.filter(Q(name__icontains=search_query))
#     paginator = Paginator(sales, 50)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     context = {
#         'page_obj': page_obj,
#         "segment": "sales"
#     }
#     html_template = loader.get_template('home/sales.html')
#     return HttpResponse(html_template.render(context, request))


# def sale_create(request):
#     if request.method == 'POST':
#         form = SaleForm(request.POST, request.FILES)
#         if form.is_valid():
#             instance = form.save()
#             required_product = Product.objects.filter(itemcode=form.cleaned_data['required_product']).first()
#             gift_product = Product.objects.filter(itemcode=form.cleaned_data['required_product']).first()
#             instance.product = required_product
#             instance.gift_product = gift_product
#             instance.save()
#             return redirect('home_sales')
#     else:
#         form = SaleForm()

#     return render(request,
#                   'home/sale_create.html',
#                   {'form': form})


# @login_required(login_url="/login/")
# def sale_detail(request, pk):
#     sale = Sale.objects.get(id=pk)

#     if request.method == 'POST':
#         form = SaleForm(request.POST, request.FILES, instance=sale)
#         if form.is_valid():
#             instance = form.save()
#             required_product = Product.objects.filter(itemcode=form.cleaned_data['required_product']).first()
#             gift_product = Product.objects.filter(itemcode=form.cleaned_data['required_product']).first()
#             instance.product = required_product
#             instance.gift_product = gift_product
#             instance.save()
#             return redirect('home_sales')
#     else:
#         form = SaleForm(instance=sale)

#     return render(request,
#                   'home/sale_detail.html',
#                   {'form': form, 'segment': 'sales', 'sale': sale})


# class SaleDelete(DeleteView):
#     model = Sale
#     fields = '__all__'
#     success_url = reverse_lazy('home_sales')


# def story_categories(request):
#     story_category = StoryCategory.objects.all().order_by('index')
#     search_query = request.GET.get('q')
#     if search_query:
#         story_category = story_category.filter(Q(name__icontains=search_query))
#     paginator = Paginator(story_category, 50)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
#     context = {
#         'page_obj': page_obj,
#         "segment": "story_category"
#     }
#     html_template = loader.get_template('home/story_categories.html')
#     return HttpResponse(html_template.render(context, request))


# def story_category_create(request):
#     if request.method == 'POST':
#         form = StoryCategoryForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('home_story_category')
#     else:
#         form = StoryCategoryForm()

#     return render(request,
#                   'home/story_category_create.html',
#                   {'form': form})


# @login_required(login_url="/login/")
# def story_category_detail(request, pk):
#     story_category = StoryCategory.objects.get(id=pk)

#     if request.method == 'POST':
#         form = StoryCategoryForm(request.POST, request.FILES, instance=story_category)
#         if form.is_valid():
#             form.save()
#             return redirect('home_story_category')
#     else:
#         form = StoryCategoryForm(instance=story_category)

#     return render(request,
#                   'home/story_category_detail.html',
#                   {'form': form, 'segment': 'story_category', 'sale': story_category})


# class StoryCategoryDelete(DeleteView):
#     model = StoryCategory
#     fields = '__all__'
#     success_url = reverse_lazy('home_story_category')


