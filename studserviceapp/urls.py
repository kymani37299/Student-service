"""studserviceapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('izborgrupe/<str:username>', views.izborgrupe , name='izborgrupe'),
    path('mail/<str:username>', views.sendMail , name='mail'),
    path('changeGroup/<str:grupa>', views.changeGroup, name='changeGroup'),
    path('groupStudents', views.groupStudents, name='groupStudents'),
    path('newGroup/<str:username>', views.newGroup, name='newGroup'),
    path('addGroup', views.addGroup, name='addGroup'),
    path('izaberiGrupu',views.izaberiGrupu, name='izaberiGrupu'),
    path('changedGroup', views.changedGroup, name='changedGroup'),
    path('groupList/<str:username>', views.groupList, name='groupList'),
    path('mailSent', views.mailSent, name='mailSent'),
    path('podaciStudenta/<str:username>', views.podaciStudenta , name='podaciStudenta'),
    path('uploadSliku', views.uploadSliku , name='uploadSliku'),
    path('predajeStudentima/<str:username>', views.predajeStudentima , name='predajeStudentima'),
    path('izbornaGrupaList/<str:group>', views.izbornaGrupaList , name='izbornaGrupaList'),
    path('submitRasporedPolaganja/<str:username>', views.submitRasporedPolaganja, name='submitRasporedPolaganja'),
    path('submitRasporedPolaganja/submit', views.do_submitRasporedPolaganja, name='do_submitRasporedPolaganja'),
    path('loginResponse', views.loginResponse, name='loginResponse'),
    path('home/<str:username>', views.home, name='home'),
    path('izborGrupeDetalji/<str:username>',views.izborGrupeDetalji,name="izborGrupeDetalji"),
    path('izborGrupeDetalji_request',views.izborGrupeDetalji_request,name="izborGrupeDetalji_request"),
    path('unosObavestenja/<str:nalog>',views.unosObavestenja,name="unosObavestenja"),
    path('unesiObavestenje',views.unesiObavestenje,name="unesiObavestenje"),
    path('izborneGrupe/<str:username>',views.izborneGrupe,name="izborneGrupe"),
    path('ceoRaspored/<str:username>',views.ceoRaspored,name="ceoRaspored")
]

from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
