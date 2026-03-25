"""
URL configuration for CrmSys project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views
from userprofile.forms import LoginForm
from userprofile.views import my_logout
from core.views import index

urlpatterns = ([
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('dashboard/', include('dashboard.urls')),
    path('dashboard/', include('core.urls')),
    path('dashboard/account/', include('userprofile.urls')),
    path('dashboard/leads/', include('lead.urls')),
    path('dashboard/tasks/', include('task.urls')),
    path('dashboard/clients/', include('client.urls')),
    path('dashboard/products/', include('product.urls')),
    path('dashboard/calendar/', include('calendarapp.urls')),
    path('login/', views.LoginView.as_view(template_name='userprofile/login.html',
                                           authentication_form=LoginForm), name='login'),
    path('logout/', my_logout, name='logout'),
])+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
