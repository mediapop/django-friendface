from django.contrib import admin
from accounts.models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('facebook',)


admin.site.register(UserProfile, UserProfileAdmin)
