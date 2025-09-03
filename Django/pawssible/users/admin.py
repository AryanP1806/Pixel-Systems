from django.contrib import admin
from .models import Profile
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PetSchedule

admin.site.register(Profile)


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_staff', 'phone_number']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'profile_image')}),
    )

admin.site.register(CustomUser, CustomUserAdmin )
admin.site.register(PetSchedule )
