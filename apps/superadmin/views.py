import datetime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from apps.authentication.models import *
from apps.superadmin.forms import *
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy


@login_required(login_url="/login/")
def filials(request):

    if not request.user.is_superuser:
        return redirect('/login/')
    
    all_filials = Filial.objects.all()
    search_query = request.GET.get('q')
    if search_query:
        all_filials = all_filials.filter(Q(name__icontains=search_query))
    paginator = Paginator(all_filials, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        "segment": "filials"
    }
    
    html_template = loader.get_template('home/superuser/filials.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def filial_create(request):

    if not request.user.is_superuser:
        return redirect('/login/')

    if request.method == 'POST':
        form = FilialForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_filials')
    else:
        form = FilialForm()

    return render(request,
                  'home/superuser/filial_create.html',
                  {'form': form,  "segment": "filials"})


@login_required(login_url="/login/")
def filial_detail(request, pk):

    if not request.user.is_superuser:
        return redirect('/login/')

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
                  {'form': form, 'segment': 'filials', 'filial': filial})


class FilialDelete(DeleteView):
    model = Filial
    fields = '__all__'
    success_url = reverse_lazy('admin_filials')

@login_required(login_url="/login/")
def admin_list(request):
    if not request.user.is_superuser:
        return redirect('/login/')
    request.session['selected_filial_id'] = 'super_admin'
    admins = Administrator.objects.select_related('user', 'filial')
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
        'segment': 'admins'
    }
    return render(request, 'home/superuser/adminstrators.html', context)

@login_required(login_url="/login/")
def admin_create(request):
    if not request.user.is_superuser:
        return redirect('/login/')

    if request.method == 'POST':
        form = AdminUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_adminstrators')
    else:
        form = AdminUserForm()

    return render(request, 'home/superuser/adminstrator_create.html', {
        'form': form,
        'segment': 'admins'
    })
    
@login_required(login_url="/login/")
def admin_detail(request, pk):
    if not request.user.is_superuser:
        return redirect('/login/')

    admin = Administrator.objects.get(id=pk)

    if request.method == 'POST':
        form = AdminUserForm(request.POST, request.FILES, instance=admin)
        if form.is_valid():
            form.save()
            return redirect('admin_adminstrators')
    else:
        form = AdminUserForm(instance=admin)

    return render(request, 'home/superuser/adminstrator_detail.html', {
        'form': form,
        'segment': 'admins',
        'admin': admin
    })
    
class AdminstratorDeleteView(DeleteView):
    model = Administrator
    success_url = reverse_lazy('admin_adminstrators')
    template_name = 'superadmin/administrator_confirm_delete.html'



def select_filial(request, filial_id):
    if request.user.is_superuser:
        print(filial_id)
        request.session['selected_filial_id'] = filial_id
    return redirect('home')
