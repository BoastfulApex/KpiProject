import datetime
from django.db.models import Q, OuterRef, Subquery, Count, Q, F
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
from django.db.models import Count
import json
from django.db.models.functions import TruncMonth, ExtractWeekDay


def build_report(start_date, end_date, filial_id=None):
    report = []
    delta = timedelta(days=1)
    if type(start_date) is str:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()


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
            
            # Agar xodim administratorning filialiga tegishli bo'lmasa, o'tkazib yuborish
            if employee.filial_id != filial_id:
                continue
            
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
    return report


def build_report_for_employee(employee_id, start_date, end_date):
    report = []
    delta = timedelta(days=1)

    if type(start_date) is str:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    current = start_date
    employee = Employee.objects.get(id=employee_id)

    while current <= end_date:
        weekday_name = calendar.day_name[current.weekday()]
        try:
            weekday_obj = Weekday.objects.get(name_en=weekday_name)
            week_uz = weekday_obj.name
        except Weekday.DoesNotExist:
            current += delta
            continue
        
        try:
            schedule = WorkSchedule.objects.get(employee=employee, weekday=weekday_obj)
        except WorkSchedule.DoesNotExist:
            current += delta
            continue

        if employee.created_at.date() > current:
            current += delta
            continue

        attendance = Attendance.objects.filter(employee=employee, date=current).first()

        status = "Kelmagan"
        check_in = "-"
        check_out = "-"
        late_minutes = "-"
        early_leave_minutes = "-"

        if attendance:
            status = "Kelgan"
            check_in = attendance.check_in
            check_out = attendance.check_out

            if check_in and check_in > schedule.start:
                late_delta = datetime.combine(current, check_in) - datetime.combine(current, schedule.start)
                late_minutes = int(late_delta.total_seconds() / 60)
            else:
                late_minutes = 0

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

    return report


def index(request):
    # if not request.user.is_authenticated:
    #     return redirect('/login/')
    # data = {}
    # filial = ''
    # admin = None
    # tashkent_time = timezone.localtime(timezone.now())
    # if request.user.is_superuser:
    #     filials = Filial.objects.all()
    #     data['filials'] = filials
    #     selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
    #     data['selected_filial_id'] = selected_filial_id
    #     template = 'home/superuser/super_dashboard.html'
    #     try:
    #         filial = Filial.objects.get(id=int(selected_filial_id)).filial_name
    #     except:
    #         filial = ''
    # elif not request.user.is_superuser:
    #     template = 'home/user/staff_dashboard.html'
    #     admin = Administrator.objects.get(user=request.user)
    #     selected_filial_id = admin.filial.id
    #     filial = admin.filial.filial_name
    # else:
    #     return redirect('/login/')

    # today = timezone.now().date()
    # start_date = today - timedelta(days=6)
    # attendance_stats = (
    #     Attendance.objects
    #     .filter(date__range=[start_date, today], employee__filial_id=selected_filial_id)
    #     .order_by('date')
    # )

    # labels = [item['date'].strftime('%d-%m') for item in attendance_stats]
    # values = [item['total'] for item in attendance_stats]
    # print(len(values))

    # context = {
    #     'segment': 'dashboard',
    #     'data': data,
    #     "filial": filial,
    #     'tashkent_time': tashkent_time,
    #     'chart_labels': json.dumps(labels),
    #     'chart_values': json.dumps(values),
    # }

    # html_template = loader.get_template(template)
    # return HttpResponse(html_template.render(context, request))
    # if not request.user.is_authenticated:
    #     return redirect('/login/')
    # data = {}
    # template = ''
    # late_count = 0
    # early_leave_count = 0
    # total_attendance_count = 0
    # todays_attendance_count = 0
    # early_leave_percent = 0
    # late_percent = 0
    # filial = None
    # admin = None
    # tashkent_time = timezone.localtime(timezone.now())
    # selected_filial_id = request.session.get('selected_filial_id', 'super_admin')

    # if request.user.is_superuser:
    #     filials = Filial.objects.all()
    #     data['filials'] = filials
    #     template = 'home/superuser/super_dashboard.html'

    # else :
    #     try:
    #         admin = Administrator.objects.get(user=request.user)
    #         selected_filial_id = admin.filial.id
    #         template = 'home/user/staff_dashboard.html'
    #     except Administrator.DoesNotExist:
    #         selected_filial_id = None

    #     filial = Filial.objects.get(id=selected_filial_id) if selected_filial_id else None

    #     today = timezone.localdate()
    #     week_start = today - timedelta(days=6)

    #     # 🔹 Bugungi kelgan xodimlar soni
    #     todays_attendance_count = Attendance.objects.filter(
    #         employee__filial=filial,
    #         date=today
    #     ).count()

    #     attendances = Attendance.objects.filter(
    #         employee__filial=filial,
    #         date__range=[week_start, today]
    #     ).select_related('employee')

    #     for att in attendances:
    #         total_attendance_count += 1
    #         schedule = WorkSchedule.objects.filter(employee=att.employee).first()
    #         if schedule:
    #             if att.check_in and att.check_in > schedule.start:  # kech kelgan
    #                 late_count += 1
    #             if att.check_out and att.check_out < schedule.end:  # erta ketgan
    #                 early_leave_count += 1

    #     late_percent = (late_count / total_attendance_count * 100) if total_attendance_count > 0 else 0
    #     early_leave_percent = (early_leave_count / total_attendance_count * 100) if total_attendance_count > 0 else 0

    # context = {
    #     'segment': 'dashboard',
    #     'data': data,
    #     "filial": filial.filial_name if filial is not None else "",
    #     'tashkent_time': tashkent_time,
    #     'todays_attendance_count': todays_attendance_count,
    #     'late_percent': round(late_percent, 1),
    #     'early_leave_percent': round(early_leave_percent, 1),
    # }

    if not request.user.is_authenticated:
        return redirect('/login/')
    data = {}
    filial = ''
    admin = None
    total_attendance_count = 0
    todays_attendance_count = 0
    early_leave_percent = 0
    late_percent = 0
    late_count = 0
    early_leave_count = 0
    chart_labels = []
    late_values = []
    early_values = []

    tashkent_time = timezone.localtime(timezone.now())
    selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
    print(selected_filial_id)
    if request.user.is_superuser:
        filials = Filial.objects.all()
        data['filials'] = filials
        data['selected_filial_id'] = selected_filial_id
        template = 'home/superuser/super_dashboard.html'
        try:
            filial = Filial.objects.get(id=int(selected_filial_id))
        except:
            filial = ''
    elif not request.user.is_superuser:

        template = 'home/user/staff_dashboard.html'
        admin = Administrator.objects.get(user=request.user)
        filial = admin.filial
    else:
        return redirect('/login/')
    
    if selected_filial_id  != 'super_admin':
        today = timezone.localdate()
        print('aaaaa')
        week_start = today - timedelta(days=6)

        # 🔹 Bugungi kelgan xodimlar soni
        todays_attendance_count = Attendance.objects.filter(
            employee__filial=filial,
            date=today
        ).count()

        attendances = Attendance.objects.filter(
            employee__filial=filial,
            date__range=[week_start, today]
        ).select_related('employee')

        for att in attendances:
            total_attendance_count += 1
            schedule = WorkSchedule.objects.filter(employee=att.employee).first()
            if schedule:
                if att.check_in and att.check_in > schedule.start:  # kech kelgan
                    late_count += 1
                if att.check_out and att.check_out < schedule.end:  # erta ketgan
                    early_leave_count += 1

        late_percent = (late_count / total_attendance_count * 100) if total_attendance_count > 0 else 0
        early_leave_percent = (early_leave_count / total_attendance_count * 100) if total_attendance_count > 0 else 0

        six_months_ago = timezone.localdate().replace(day=1) - timedelta(days=150)

        # WorkSchedule dan xodim va haftaning kuni bo‘yicha mos start/end vaqtlarni olish
        schedule_qs = WorkSchedule.objects.filter(
            employee=OuterRef('employee'),
            weekday__id=ExtractWeekDay(OuterRef('date'))  # haftaning kuni mos
        )

        monthly_data = (
            Attendance.objects.filter(
                employee__filial=filial,
                date__gte=six_months_ago
            )
            .annotate(
                schedule_start=Subquery(schedule_qs.values('start')[:1]),
                schedule_end=Subquery(schedule_qs.values('end')[:1]),
                month=TruncMonth('date')
            )
            .values('month')
            .annotate(
                total=Count('id'),
                late_count=Count('id', filter=Q(check_in__gt=F('schedule_start'))),
                early_count=Count('id', filter=Q(check_out__lt=F('schedule_end')))
            )
            .order_by('month')
        )   
        
        for entry in monthly_data:
            month_name = entry['month'].strftime('%b %Y')
            chart_labels.append(month_name)
            if entry['total'] > 0:
                late_percent_val = round(entry['late_count'] / entry['total'] * 100, 1)
                early_percent_val = round(entry['early_count'] / entry['total'] * 100, 1)
            else:
                late_percent_val = early_percent_val = 0
            late_values.append(late_percent_val)
            early_values.append(early_percent_val)
            
        template = 'home/user/staff_dashboard.html'

    context = {
        'segment': 'dashboard',
        'data': data,
        "filial": filial,
        'tashkent_time': tashkent_time,
        'todays_attendance_count': todays_attendance_count,
        'late_percent': round(late_percent, 1),
        'early_leave_percent': round(early_leave_percent, 1),

    }
    context['chart_labels_json'] = json.dumps(chart_labels)
    context['late_values_json'] = json.dumps(late_values)
    context['early_values_json'] = json.dumps(early_values)
    print(context['late_values_json'])
    html_template = loader.get_template(template)
    return HttpResponse(html_template.render(context, request))




@login_required(login_url="/login/")
def employees(request):
    administrator = None
    filial = ''
    data = {}
    filials = Filial.objects.all()
    data['filials'] = filials
    selected_filial_id = ''
    if request.user.is_superuser:
        selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
        if selected_filial_id == 'super_admin':
            return redirect('/home/')
        filial_id = selected_filial_id
    else:
        administrator = Administrator.objects.get(user=request.user)
        filial_id = administrator.filial.id
    employees = Employee.objects.filter(filial_id = filial_id)
    search_query = request.GET.get('q')
    filial = Filial.objects.get(id=filial_id)
    if search_query:
        employees = employees.filter(Q(name__icontains=search_query))
    paginator = Paginator(employees, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    tashkent_time = timezone.localtime(timezone.now())

    context = {
        'page_obj': page_obj,
        "segment": "employees",
        "filial": filial.filial_name,
        'tashkent_time': tashkent_time,
        'data': data
    }
    html_template = loader.get_template('home/user/employees/employees.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def employee_create(request):
    filial_id = ''
    data = {}
    filials = Filial.objects.all()
    data['filials'] = filials
    selected_filial_id = ''
    if request.user.is_superuser:
        selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
        if selected_filial_id == 'super_admin':
            return redirect('/home/')
        filial_id = selected_filial_id
    else:
        filial_id = Administrator.objects.get(user=request.user).filial.id
        

    tashkent_time = timezone.localtime(timezone.now())
    filial = Filial.objects.get(id=int(filial_id))
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            # return redirect('employees')
            employee.filial = filial
            if 'image' in request.FILES:
                employee.image = request.FILES['image']
            employee.save()          
            return redirect(reverse('create_schedule_for_employee', args=[employee.id]))    
    else:
        form = EmployeeForm()

    return render(request,
                  'home/user/employees/employee_create.html',
                  {'form': form,
                   "filial": filial.filial_name,
                   "segment": "employees",
                   'data': data,
        'tashkent_time': tashkent_time})


@login_required(login_url="/login/")
def employee_detail(request, pk):
    filial_id = ''
    data = {}
    filials = Filial.objects.all()
    data['filials'] = filials
    selected_filial_id = ''
    if request.user.is_superuser:
        selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
        if selected_filial_id == 'super_admin':
            return redirect('/home/')
        filial_id = selected_filial_id
    else:
        filial_id = Administrator.objects.get(user=request.user).filial.id
    employee = Employee.objects.get(id=pk)
    tashkent_time = timezone.localtime(timezone.now())
    if employee.filial_id != int(filial_id):
        return redirect('home')
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save(commit=False)  # instance olamiz
            if 'image' in request.FILES:
                employee.image = request.FILES['image']  # faylni biriktiramiz
            employee.save()
        return redirect('employees')
    else:
        form = EmployeeForm(instance=employee)

    return render(request,
                  'home/user/employees/employee_detail.html',
                  {'form': form, 'segment': 'employees', 
                   'employee': employee, 
                   'filial': employee.filial.filial_name, 
                   'tashkent_time': tashkent_time,
                   'data': data})


class EmployeeDelete(DeleteView):
    model = Employee
    fields = '__all__'
    success_url = reverse_lazy('employees')


@login_required(login_url="/login/")
def schedules(request):
    filial_id = ''
    data = {}
    filial_name = ''
    filials = Filial.objects.all()
    data['filials'] = filials
    selected_filial_id = ''
    if request.user.is_superuser:
        selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
        if selected_filial_id == 'super_admin':
            return redirect('/home/')
        filial_id = selected_filial_id    
    else:
        filial_id = Administrator.objects.get(user=request.user).filial.id
        filial_name = Administrator.objects.get(user=request.user).filial.filial_name
    tashkent_time = timezone.localtime(timezone.now())
    
    all_schedules = WorkSchedule.objects.filter(employee__filial__id= filial_id)
    search_query = request.GET.get('q')
    if search_query:
        all_schedules = all_schedules.filter(Q(name__icontains=search_query))
    paginator = Paginator(all_schedules, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        "segment": "schedules",
        "filial": filial_name,
        'tashkent_time': tashkent_time,
        'data': data
    }
    html_template = loader.get_template('home/user/workschedule/schedules.html')
    return HttpResponse(html_template.render(context, request))


def create_schedule_for_employee(request, employee_id):
    filial_id = ''
    data = {}
    filial_name = ''
    filials = Filial.objects.all()
    data['filials'] = filials
    selected_filial_id = ''
    employee = get_object_or_404(Employee, id=employee_id)
    if request.user.is_superuser:
        selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
        if selected_filial_id == 'super_admin' or employee.filial_id != int(selected_filial_id):
            return redirect('/home/')
        filial_id = selected_filial_id    
    else:
        filial_id = Administrator.objects.get(user=request.user).filial.id
        filial_name = Administrator.objects.get(user=request.user).filial.filial_name
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
                  {'form': form, 'employee': employee, 'filial': employee.filial.filial_name, 'data': data,
                   'tashkent_time': tashkent_time})

    
@login_required(login_url="/login/")
def create_schedule(request):
    filial_id = ''
    data = {}
    filial_name = ''
    filials = Filial.objects.all()
    data['filials'] = filials
    selected_filial_id = ''
    if request.user.is_superuser:
        selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
        if selected_filial_id == 'super_admin':
            return redirect('/home/')
        filial_id = selected_filial_id
    else:
        filial_id = Administrator.objects.get(user=request.user).filial.id
        filial_name = Administrator.objects.get(user=request.user).filial.filial_name
    tashkent_time = timezone.localtime(timezone.now())
    filial = Filial.objects.get(id=int(filial_id))
    administrator = Administrator.objects.filter(filial=filial).first()
    if request.method == 'POST':
        form = WorkScheduleWithUserForm(request.POST, admin=administrator)
        if form.is_valid():
            form.save()
            return redirect('schedules')
    else:
        form = WorkScheduleWithUserForm(admin=administrator)
    return render(request, 'home/user/workschedule/schedule_create.html', 
                  {'form': form, 
                   "filial": filial_name,
                   "segment": "schedules",  'tashkent_time': tashkent_time, 'data': data})


class WorkScheduleDelete(DeleteView):
    model = WorkSchedule
    fields = '__all__'
    success_url = reverse_lazy('schedules')


def get_report_date(request):
    report = []
    page_obj = []
    filial_id = ''
    data = {}
    filial_name = ''
    filials = Filial.objects.all()
    data['filials'] = filials
    selected_filial_id = ''
    if request.user.is_superuser:
        selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
        if selected_filial_id == 'super_admin':
            return redirect('/home/')
        filial_id = int(selected_filial_id)
    else:
        filial_id = Administrator.objects.get(user=request.user).filial.id
        filial_name = Administrator.objects.get(user=request.user).filial.filial_name
    tashkent_time = timezone.localtime(timezone.now())
    
    if request.method == 'POST':
        form = AttendanceDateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            report = build_report(start_date=start_date, end_date=end_date, filial_id=filial_id)
        paginator = Paginator(report, 5)  # Har bir sahifada 20 ta yozuv

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    else:
        form = AttendanceDateRangeForm()
    
    return render(request, 'home/user/report/get_report_date.html', {'form': form, 
                                                                     'report': report, 
                                                                     'segment': 'report',
                                                                     'tashkent_time': tashkent_time,
                                                                     'filial': filial_name,
                                                                     'data': data})


import openpyxl
from django.http import HttpResponse

def download_excel(request):
    filial_id = ''
    data = {}
    filials = Filial.objects.all()
    data['filials'] = filials
    selected_filial_id = ''
    if request.user.is_superuser:
        selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
        if selected_filial_id == 'super_admin':
            return redirect('/home/')
        filial_id = int(selected_filial_id)
    else:
        filial_id = Administrator.objects.get(user=request.user).filial.id

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        return redirect('home_get_dates')

    data = build_report(start_date=start_date, end_date=end_date, filial_id=filial_id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['Sana', 'Hafta kuni', 'Xodim', 'Holati', 'Jadval', 'Kirish', 'Chiqish', 'Kechikdi', 'Erta ketdi'])

    for row in data:
        ws.append([
            row['date'], row['weekday'], row['employee'], row['status'],
            f"{row['schedule_start']} - {row['schedule_end']}",
            row['check_in'], row['check_out'], row['late_minutes'], row['early_leave_minutes']
        ])

    # Javobni sozlash
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=hisobot.xlsx'
    wb.save(response)
    return response


def employee_report(request, pk):
    employee = Employee.objects.get(id=pk)
    report = []
    page_obj = []
    filial_id = ''
    data = {}
    filial_name = ''
    filials = Filial.objects.all()
    data['filials'] = filials
    selected_filial_id = ''
    if request.user.is_superuser:
        selected_filial_id = request.session.get('selected_filial_id', 'super_admin')
        if selected_filial_id == 'super_admin':
            return redirect('/home/')
        filial_id = selected_filial_id
    else:
        filial_id = Administrator.objects.get(user=request.user).filial.id
        filial_name = Administrator.objects.get(user=request.user).filial.filial_name
    tashkent_time = timezone.localtime(timezone.now())
    
    if request.method == 'POST':
        form = AttendanceDateRangeForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            report = build_report_for_employee(pk, start_date, end_date)

    else:
        form = AttendanceDateRangeForm()
        
    return render(request, 'home/user/report/get_report_date.html', {
        'employee': employee,
        'form': form,
        'report': report,
        'tashkent_time': tashkent_time,
        'filial': filial_name,
        'segment': 'employees',
        'data': data
    })


def employee_download_excel(request, pk):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        return redirect('home_get_dates')

    data = build_report_for_employee(pk, start_date, end_date)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['Sana', 'Hafta kuni', 'Xodim', 'Holati', 'Jadval', 'Kirish', 'Chiqish', 'Kechikdi', 'Erta ketdi'])

    for row in data:
        ws.append([
            row['date'], row['weekday'], row['employee'], row['status'],
            f"{row['schedule_start']} - {row['schedule_end']}",
            row['check_in'], row['check_out'], row['late_minutes'], row['early_leave_minutes']
        ])

    # Javobni sozlash
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=hisobot.xlsx'
    wb.save(response)
    return response
