from django import forms
from .models import *

class FilialForm(forms.ModelForm):

    filial_name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Nomi",
                "class": "form-control",
            }
        ))

    class Meta:
        model = Filial
        fields = '__all__'


class AdminUserForm(forms.ModelForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Foydalanuvchi nomi"
        })
    )

    password = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Parol kiriting"
        })
    )

    telegram_id = forms.IntegerField(
        label="Telegram ID (user_id)",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Telegram user_id"
        })
    )

    full_name = forms.CharField(
        label="To‘liq ism",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Ism Familiya"
        })
    )

    filial = forms.ModelChoiceField(
        queryset=Filial.objects.all(),
        label="Filial",
        widget=forms.Select(attrs={
            "class": "form-control"
        })
    )

    class Meta:
        model = Administrator
        fields = ['telegram_id', 'full_name', 'filial']

    def save(self, commit=True):
        # Agar instance mavjud bo'lsa, mavjud userni yangilaymiz
        if self.instance and self.instance.user:
            user = self.instance.user  # Mavjud user
            user.username = self.cleaned_data['username']
            user.first_name = self.cleaned_data['full_name']
            # Agar parol kiritilgan bo'lsa, yangilaymiz
            if self.cleaned_data['password']:
                user.set_password(self.cleaned_data['password'])
            user.is_staff = True
            user.is_superuser = False
            if commit:
                user.save()
        else:
            # Yangi user yaratish
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['full_name'],
            )
            user.is_staff = True
            user.is_superuser = False
            if commit:
                user.save()

        admin = super().save(commit=False)
        admin.user = user
        admin.telegram_id = self.cleaned_data['telegram_id']
        admin.full_name = self.cleaned_data['full_name']
        admin.filial = self.cleaned_data['filial']
        if commit:
            admin.save()
        return admin