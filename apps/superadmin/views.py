import datetime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.template import loader
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from apps.authentication.models import *
from apps.superadmin.forms import *
from apps.main.forms import *
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy
import requests
from apps.superadmin.decorators import org_admin_required


@org_admin_required
def filials(request):
    data = {}
    admin_user = Administrator.objects.get(user=request.user)
    
    all_filials = Filial.objects.filter(organization=admin_user.organization).all()
    search_query = request.GET.get('q')
    data['filials'] = all_filials
    request.session['selected_filial_id'] = 'super_admin'
    if search_query:
        all_filials = all_filials.filter(Q(name__icontains=search_query))
    paginator = Paginator(all_filials, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        "segment": "filials",
        'data': data
    }
    html_template = loader.get_template('home/superuser/filials.html')
    return HttpResponse(html_template.render(context, request))

@org_admin_required
def filial_create(request):
    try:
        admin_user = Administrator.objects.get(user=request.user)
    except Administrator.DoesNotExist:
        return HttpResponseForbidden("Siz administrator emassiz.")

    if not admin_user.is_org_admin:
        return redirect('/login/')
    data = {}
    filials = Filial.objects.filter(organization=admin_user.organization).all()
    data['filials'] = filials
    print(filials)
    request.session['selected_filial_id'] = 'super_admin'

    if request.method == 'POST':
        form = FilialForm(request.POST)
        if form.is_valid():
            filial = form.save(commit=False)
            filial.organization = admin_user.organization  # avtomatik bog‘lanadi
            filial.save()
            return redirect('admin_filials')
    else:
        form = FilialForm()

    return render(request,
                  'home/superuser/filial_create.html',
                  {'form': form,  "segment": "filials", 'data': data})


@org_admin_required
def filial_detail(request, pk):
    admin_user = Administrator.objects.get(user=request.user)    
    data = {}
    filials = Filial.objects.filter(organization=admin_user.organization).all()
    data['filials'] = filials
    request.session['selected_filial_id'] = 'super_admin'    

    filial = Filial.objects.get(id=pk)

    if request.method == 'POST':
        form = FilialForm(request.POST, request.FILES, instance=filial)
        if form.is_valid():
            form.save()
            return redirect('admin_filials')
    else:
        form = FilialForm(instance=filial)

    return render(request,
                  'home/superuser/filial_detail.html',
                  {'form': form, 'segment': 'filials', 'filial': filial, 'data': data})


class FilialDelete(DeleteView):
    model = Filial
    fields = '__all__'
    success_url = reverse_lazy('admin_filials')


@org_admin_required
def admin_list(request):
    admin_user = Administrator.objects.get(user=request.user)
    data = {}
    filials = Filial.objects.all()
    data['filials'] = filials
        
    request.session['selected_filial_id'] = 'super_admin'
    admins = Administrator.objects.select_related('user', 'filial').filter(organization=admin_user.organization, is_org_admin=False).all()
    search_query = request.GET.get('q')
    if search_query:
        admins = admins.filter(
            Q(full_name__icontains=search_query) |
            Q(user__username__icontains=search_query)
        )
    paginator = Paginator(admins, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'segment': 'admins',
        'data': data
    }
    return render(request, 'home/superuser/adminstrators.html', context)


@org_admin_required
def admin_create(request):
    admin_user = Administrator.objects.get(user=request.user)
    data = {}
    filials = Filial.objects.filter(organization=admin_user.organization).all()
    data['filials'] = filials
    request.session['selected_filial_id'] = 'super_admin'
    if request.method == 'POST':
        form = AdminUserForm(request.POST, admin_user=request.admin_user)
        if form.is_valid():
            admin = form.save()
            admin.organization = admin_user.organization  # avtomatik bog‘lanadi
            admin.save()
            return redirect('admin_adminstrators')
    else:
        form = AdminUserForm(admin_user=admin_user)

    return render(request, 'home/superuser/adminstrator_create.html', {
        'form': form,
        'segment': 'admins',
        'data': data
    })

    
@org_admin_required
def admin_detail(request, pk):
    admin_user = Administrator.objects.get(user=request.user)
    admin = Administrator.objects.get(id=pk)
    data = {}
    filials = Filial.objects.all()
    data['filials'] = filials
    request.session['selected_filial_id'] = 'super_admin'
    
    if request.method == 'POST':
        form = AdminUserForm(request.POST, request.FILES, instance=admin, admin_user=admin_user)
        if form.is_valid():
            form.save()
            return redirect('admin_adminstrators')
    else:
        form = AdminUserForm(instance=admin, admin_user=admin_user)

    return render(request, 'home/superuser/adminstrator_detail.html', {
        'form': form,
        'segment': 'admins',
        'admin': admin,
        'data': data
    })

    
class AdminstratorDeleteView(DeleteView):
    model = Administrator
    success_url = reverse_lazy('admin_adminstrators')
    template_name = 'superadmin/administrator_confirm_delete.html'



@org_admin_required
def select_filial(request, filial_id):
    admin_user = Administrator.objects.get(user=request.user)
    if admin_user.is_org_admin == True:
        request.session['selected_filial_id'] = filial_id
    return redirect('home')


@org_admin_required
def locations(request):
    data = {}
    
    admin_user = Administrator.objects.get(user=request.user)    
    all_filials = Filial.objects.filter(organization=admin_user.organization).all()
    search_query = request.GET.get('q')
    data['filials'] = all_filials
    locations = Location.objects.filter(organization=admin_user.organization).all()
    request.session['selected_filial_id'] = 'super_admin'
    if search_query:
        locations = locations.filter(Q(address__icontains=search_query))
    paginator = Paginator(locations, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        "segment": "locations",
        'data': data
    }
    
    html_template = loader.get_template('home/superuser/locations.html')
    return HttpResponse(html_template.render(context, request))

from django.http import JsonResponse

def create_location_ajax(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors.as_text()})
    return JsonResponse({'success': False, 'errors': 'Noto‘g‘ri so‘rov'})

        
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def get_location_name(lat, lon):
    geolocator = Nominatim(user_agent="myuzbot (jigar@t.me)")
    try:
        location = geolocator.reverse((lat, lon), timeout=10)
        return location.address if location else "Nomaʼlum manzil"
    except GeocoderTimedOut:
        return "Geocoding vaqti tugadi"
    
@org_admin_required    
def create_location(request):
    admin_user = Administrator.objects.get(user=request.user)
    data = {}
    filials = Filial.objects.filter(organization=admin_user.organization).all()
    data['filials'] = filials

    if request.method == 'POST':
        form = LocationForm(request.POST, admin_user=admin_user)
        if form.is_valid():
            filial = form.cleaned_data.get('filial')

            # Eski location bo‘lsa, uni o‘chiramiz
            old_location = Location.objects.filter(filial=filial).all()
            if old_location.exists():
                for loc in old_location:
                    loc.delete()

            instance = form.save(commit=False)

            # Location nomini olish (masalan, reverse geocoding orqali)
            name = get_location_name(instance.latitude, instance.longitude)
            instance.name = name or "Unknown location"
            instance.address = name
            instance.organization = admin_user.organization  # avtomatik bog‘lanadi
            instance.save()

            return redirect('admin_locations')  # o'zingiz xohlagan URL nomi
    else:
        form = LocationForm(admin_user=admin_user)

    return render(request, 'home/superuser/location_create.html', {'form': form, 'data': data, 'segment': 'locations'})

    
class LocationDeleteView(DeleteView):
    model = Location
    success_url = reverse_lazy('admin_locations')
    template_name = 'main/location_confirm_delete.html'

