from .models import Administrator

def admin_context(request):
    is_org_admin = False
    admin_user = None

    if request.user.is_authenticated:
        admin_user = Administrator.objects.filter(user=request.user).first()
        if admin_user:
            is_org_admin = admin_user.is_org_admin

    return {
        'is_org_admin': is_org_admin,
        'admin_user': admin_user,
    }