from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import (
    CustomUser,
    JobSeekerProfile,
    EmployerProfile,
    Resume,
    Job,
    Application,
    MatchScore,
)


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'role', 'password1', 'password2', 'is_staff', 'is_active'),
            },
        ),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(JobSeekerProfile)
admin.site.register(EmployerProfile)
admin.site.register(Resume)
admin.site.register(Job)
admin.site.register(Application)
admin.site.register(MatchScore)
