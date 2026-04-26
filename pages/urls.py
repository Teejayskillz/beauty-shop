from django.urls import path
from .views import home_view, agreement_view, agreements_view, contract_agreement_view, contract_success_view

urlpatterns = [
    path('', home_view, name='home'),
    path('agreement/', agreement_view, name='agreement'),
    path('agreements/', agreements_view, name='agreements'),
    path('contract/', contract_agreement_view, name='contract_agreement'),
    path('contract/success/', contract_success_view, name='contract_success'),
]
  