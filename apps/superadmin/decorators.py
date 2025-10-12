from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import Administrator

def org_admin_required(view_func):
    """
    Faqat organization adminlari uchun decorator.
    Agar foydalanuvchi admin bo‘lmasa yoki organization admin bo‘lmasa,
    login sahifasiga qaytaradi va alert chiqaradi.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 🔹 1. Agar foydalanuvchi login bo‘lmagan bo‘lsa
        if not request.user.is_authenticated:
            messages.warning(request, "Avval tizimga kiring.")
            return redirect('/login/')

        # 🔹 2. Administrator mavjudligini tekshiramiz
        from django.http import HttpResponseForbidden
        try:
            admin_user = Administrator.objects.get(user=request.user)
        except Administrator.DoesNotExist:
            messages.error(request, "Siz administrator emassiz.")
            return redirect('/login/')

        # 🔹 3. Faqat organization adminlar kirishi mumkin
        if not admin_user.is_org_admin:
            messages.error(request, "Sizda bu sahifaga kirish huquqi yo‘q.")
            return redirect('/login/')

        # ✅ 4. Agar hammasi joyida bo‘lsa
        request.admin_user = admin_user
        return view_func(request, *args, **kwargs)
    return _wrapped_view
