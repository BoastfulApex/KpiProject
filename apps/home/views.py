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
from datetime import timedelta, datetime
import calendar
from django.core.paginator import Paginator


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


def get_report_date(request):
    report = []
    page_obj = []
    
    if request.method == 'POST':
        form = AttendanceDateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            delta = timedelta(days=1)

            current = start_date
            while current <= end_date:
                weekday_name = calendar.day_name[current.weekday()]  # e.g. 'Monday'
                # Weekday obyektini olish
                try:
                    weekday_obj = Weekday.objects.get(name_en=weekday_name)
                    week_uz = weekday_obj.name
                except Weekday.DoesNotExist:
                    current += delta
                    continue

                # Ushbu kunda ishlashi kerak bo'lgan xodimlar
                schedules = WorkSchedule.objects.filter(weekday=weekday_obj).select_related('employee')

                for schedule in schedules:
                    employee = schedule.employee
                    if employee.created_at.date() > current:
                        continue
                    attendance = Attendance.objects.filter(employee=employee, date=current).first()

                    # Default holatlar
                    status = "Kelmagan"
                    check_in = "-"
                    check_out = "-"
                    late_minutes = "-"
                    early_leave_minutes = "-"

                    if attendance:
                        status = "Kelgan"
                        check_in = attendance.check_in
                        check_out = attendance.check_out

                        # Kechikish
                        if check_in and check_in > schedule.start:
                            late_delta = datetime.combine(current, check_in) - datetime.combine(current, schedule.start)
                            late_minutes = int(late_delta.total_seconds() / 60)
                        else:
                            late_minutes = 0

                        # Erta ketish
                        if check_out and check_out < schedule.end:
                            early_delta = datetime.combine(current, schedule.end) - datetime.combine(current, check_out)
                            early_leave_minutes = int(early_delta.total_seconds() / 60)
                        else:
                            early_leave_minutes = 0

                    report.append({
                        'index': len(report) + 1,
                        'date': current,
                        'weekday': week_uz,
                        'employee': employee.name,
                        'status': status,
                        'check_in': check_in,
                        'check_out': check_out,
                        'schedule_start': schedule.start,
                        'schedule_end': schedule.end,
                        'late_minutes': late_minutes,
                        'early_leave_minutes': early_leave_minutes,
                    })

                current += delta
        paginator = Paginator(report, 20)  # Har bir sahifada 20 ta yozuv

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    else:
        form = AttendanceDateRangeForm()
    
    return render(request, 'home/user/report/get_report_date.html', {'form': form, 'report': page_obj})


def show_dates_view(request):
    start = request.session.get('start_date')
    end = request.session.get('end_date')
    return render(request, 'home/user/report/show_dates.html', {'start': start, 'end': end})

