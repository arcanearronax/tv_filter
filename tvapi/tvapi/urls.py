"""tvapi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path, re_path
from django.conf import settings
from .views import APIView

urlpatterns = [
	path('', APIView.as_view(), name='shows'),
    path('failue/', APIView.as_view(), name='failure'),
    re_path(r'^(?P<search_id>tt[0-9]{4,8})$', APIView.as_view(), name="showSearch"),
    path('tv/', APIView.as_view(), name='showIndex'),
	path('tv/<slug:show_id>/', APIView.as_view(), name='showView'),
	path('tv/<slug:show_id>/season/<slug:season>/', APIView.as_view(), name='seasonView'),
	path('tv/<slug:show_id>/season/<slug:season>/episode/<slug:episode>/', APIView.as_view(), name='episodeView'),
    #path('test/', APIView.test_view, name='test'),
    path('admin/', admin.site.urls),
]
