from django.contrib import admin

from .models import User, Department, Vacation, DepartmentManager

admin.site.register(User)
admin.site.register(Department)
admin.site.register(Vacation)
admin.site.register(DepartmentManager)

admin.sites.site.site_url = "HRVM.com"
admin.sites.site.name = "HRVM"
admin.sites.site.site_title = "HRVM"
admin.sites.site.site_header = "HRVM"

