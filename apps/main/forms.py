from django import forms
from .models import *



class AdminsForm(forms.ModelForm):

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ism",
                "class": "form-control",
            }
        ))
    user_id = forms.FloatField(
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Telegram UserID",
                "class": "form-control",
            }
        ))

    class Meta:
        model = Administrator
        fields = '__all__'


class EmployeeForm(forms.ModelForm):

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ism",
                "class": "form-control",
            }
        ))
    user_id = forms.FloatField(
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Telegram UserID",
                "class": "form-control",
            }
        ))
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
            }
        )
    )
    class Meta:
        model = Employee
        fields = ['name', 'user_id']


class WorkScheduleForm(forms.ModelForm):
    weekday = forms.ModelMultipleChoiceField(
        queryset=Weekday.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )
    start = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time", "style": "width: 150px;"})
    )
    end = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time", "style": "width: 150px;"})
    )

    class Meta:
        model = WorkSchedule
        fields = ['weekday', 'start', 'end']


class WorkScheduleWithUserForm(forms.ModelForm):
    
    weekday = forms.ModelMultipleChoiceField(
        queryset=Weekday.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )
    
    start = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time", "style": "width: 150px;"})
    )
    end = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time", "style": "width: 150px;"})
    )

    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        label="Employee",
        widget=forms.Select(attrs={
            "class": "form-control"
        })
    )

    class Meta:
        model = WorkSchedule
        fields = ['weekday', 'start', 'end', 'employee']

    def __init__(self, *args, **kwargs):
        admin = kwargs.pop('admin', None)  # tashqaridan admin yuboriladi
        super().__init__(*args, **kwargs)
        print(admin.filial.filial_name)
        # employee querysetni admin.filial ga qarab filtrlaymiz
        if admin and admin.filial:
            self.fields['employee'].queryset = Employee.objects.filter(filial=admin.filial)
            print(len(self.fields['employee'].queryset))
        else:
            self.fields['employee'].queryset = Employee.objects.none()  # hech narsa ko‘rsatmaydi

        self.fields['employee'].widget.attrs.update({'class': 'form-control'})
        

class AttendanceDateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control datepicker", "placeholder": "Boshlanish sanasi"})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control datepicker", "placeholder": "Tugash sanasi"})
    )


class LocationForm(forms.ModelForm):
    filial = forms.ModelChoiceField(
        queryset=Filial.objects.none(),
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
    )
    address = forms.CharField(
        widget=forms.TextInput(attrs={
            "placeholder": "To‘liq manzil avtomatik to‘ladi",
            "class": "form-control",
            "readonly": "readonly",
        }),
        required=False,
    )
    latitude = forms.FloatField(widget=forms.HiddenInput())
    longitude = forms.FloatField(widget=forms.HiddenInput())

    class Meta:
        model = Location
        fields = ['filial', 'latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        admin_user = kwargs.pop('admin_user', None)
        super().__init__(*args, **kwargs)

        if admin_user and hasattr(admin_user, 'organization'):
            self.fields['filial'].queryset = Filial.objects.filter(
                organization=admin_user.organization
            )
        else:
            self.fields['filial'].queryset = Filial.objects.none()


# class CategoryForm(forms.ModelForm):
#     groupname = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "placeholder": "Slider nomi uz",
#                 "class": "form-control",
#                 'readonly': 'readonly'
#             }
#         ))

#     number = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "placeholder": "Slider nomi ru",
#                 "class": "form-control",
#                 'readonly': 'readonly',
#     }
#         ))
#     image = forms.ImageField(
#       widget=forms.FileInput()
#     )

#     class Meta:
#         model = Category
#         fields = "__all__"


# class SubCategoryForm(forms.ModelForm):
#     name = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "placeholder": "Slider nomi uz",
#                 "class": "form-control",
#                 'readonly': 'readonly'
#             }
#         ))

#     code = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#                 'readonly': 'readonly',
#             }
#         ))

#     category = forms.ModelChoiceField(
#         widget=forms.Select(
#             attrs={
#                 "class": "form-control",
#                 'readonly': 'readonly'
#             }
#         ),
#         queryset=Category.objects.all())

#     image = forms.ImageField(
#       widget=forms.FileInput()
#     )

#     class Meta:
#         model = SubCategory
#         fields = "__all__"


# class ManufacturerForm(forms.ModelForm):
#     manufacturer_name = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#                 'readonly': 'readonly'
#             }
#         ))

#     code = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#                 'readonly': 'readonly',
#             }
#         ))
#     image = forms.ImageField(
#       widget=forms.FileInput()
#     )

#     class Meta:
#         model = Category
#         fields = "__all__"


# class ProductForm(forms.ModelForm):
#     itemname = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#         ))
#     itemcode = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#         ))
#     description = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "placeholder": "Maxsulot izohi",
#                 "class": "form-control",
#             }
#         ))
#     price = forms.FloatField(
#         widget=forms.NumberInput(
#             attrs={
#                 "placeholder": "Maxsulot narxi",
#                 "class": "form-control",
#             }
#         ))
#     image = forms.ImageField(
#       widget=forms.FileInput()
#     )
#     top = forms.BooleanField(
#         label="Top 100",
#         required=False,
#         initial=False,
#         widget=forms.CheckboxInput(attrs={'class': 'custom-class'}),
#     )

#     class Meta:
#         model = Product
#         fields = ["itemname", "itemcode", "description", "price", "image", "top"]


# class CashbackForm(forms.ModelForm):
#     PERIOD_TYPES = (
#         (MONTH, MONTH),
#         (SEASON, SEASON),
#         (YEAR, YEAR)
#     )

#     name = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#         ))
#     period = forms.ChoiceField(
#         choices=PERIOD_TYPES,
#         widget=forms.Select(
#             attrs={
#                 "class": "form-control",
#                 'readonly': 'readonly'
#             }
#         ))
#     summa = forms.FloatField(
#         widget=forms.NumberInput(
#             attrs={
#                 "placeholder": "Summa",
#                 "class": "form-control",
#             }
#         ))
#     persent = forms.FloatField(
#         widget=forms.NumberInput(
#             attrs={
#                 "placeholder": "Summa",
#                 "class": "form-control",
#             }
#         ))

#     class Meta:
#         model = Product
#         fields = ["name", "summa", "period", "persent"]


# class NotificationForm(forms.ModelForm):
#     name = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "placeholder": "Bildirishnoma Sarlavhasi",
#                 "class": "form-control",
#             }
#         ))

#     message = forms.CharField(
#         widget=forms.Textarea(
#             attrs=
#             {
#                 "placeholder": "Xabar matni",
#                 "class": "form-control",
#             }
#         ))

#     class Meta:
#         model = Notification
#         fields = '__all__'


# class SaleForm(forms.ModelForm):
#     name = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#         ))
#     expiration_date = forms.DateField(
#         widget=forms.DateInput(
#             attrs={
#                 "class": "form-control",
#                 "type": "date",
#                 "style": "width: 200px;"
#             }
#         )
#     )
#     required_product = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#         ))
#     required_quantity = forms.FloatField(
#         widget=forms.NumberInput(
#             attrs={
#                 "placeholder": "Kerakli miqdor",
#                 "class": "form-control",
#             }
#         ))
#     gift_quantity = forms.FloatField(
#         widget=forms.NumberInput(
#             attrs={
#                 "placeholder": "Sovg'a miqdori",
#                 "class": "form-control",
#             }
#         ))
#     gift_product = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#         ))

#     image = forms.ImageField(
#       widget=forms.FileInput()
#     )

#     description = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#     ))

#     class Meta:
#         model = Sale
#         fields = ["name", "expiration_date", "required_quantity", "gift_quantity", 'image', 'description']


# class StoryCategoryForm(forms.ModelForm):
#     name = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#         ))
#     image = forms.ImageField(
#       widget=forms.FileInput()
#     )
#     index = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#         ))

#     class Meta:
#         model = StoryCategory
#         fields = '__all__'


# class StoryForm(forms.ModelForm):
#     title = forms.CharField(
#         widget=forms.TextInput(
#             attrs={
#                 "class": "form-control",
#             }
#         ))
#     file = forms.FileField(
#       widget=forms.FileInput(
#           attrs={
#               "class": "form-control-file",
#           }
#       )
#     )
#     story_category = forms.ModelChoiceField(
#         widget=forms.Select(
#             attrs={
#                 "class": "form-control",
#             }
#         ),
#         queryset=StoryCategory.objects.all(),
#         empty_label=None
#     )

#     class Meta:
#         model = Story
#         fields = '__all__'

#     # def __init__(self, *args, **kwargs):
#     #     super(StoryForm, self).__init__(*args, **kwargs)
#     #     self.fields['story_category'].choices = [(category.id, category.name) for category in StoryCategory.objects.all()]
