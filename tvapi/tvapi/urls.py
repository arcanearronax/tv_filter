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
from django.urls import path
from django.conf import settings
from .views import APIView

urlpatterns = [
	path('', APIView.as_view(), name='apiview'),
	path('shows', APIView.as_view(), name='showTest'),
	path('tv/<int:show_id>/', APIView.as_view(), name='showView'),
	path('tv/<int:show_id>/season/<int:season>/', APIView.as_view(), name='seasonView'),
	path('tv/<int:show_id>/season/<int:season>/episode/<int:episode>/', APIView.as_view(), name='episodeView'),
    path('admin/', admin.site.urls),
] #+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
