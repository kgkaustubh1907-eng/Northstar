from django.contrib import admin
from django.urls import include, path
from hospital.views import login
urlpatterns = [path("admin/", admin.site.urls), path("api/auth/token/", login), path("api/", include("hospital.urls"))]
