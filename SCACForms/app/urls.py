from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.IQ5010.as_view())
]