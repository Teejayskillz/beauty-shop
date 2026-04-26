from django.urls import path
from .views import home_view, agreement_view, agreements_view, contract_agreement_view, contract_success_view, contract_list_view, contract_detail_view, contract_logout_view

urlpatterns = [
    path('', home_view, name='home'),
    path('agreement/', agreement_view, name='agreement'),
    path('agreements/', agreements_view, name='agreements'),
    path('contract/', contract_agreement_view, name='contract_agreement'),
    path('contract/success/', contract_success_view, name='contract_success'),
    path('contracts/', contract_list_view, name='contract_list'),
    path('contracts/<int:contract_id>/', contract_detail_view, name='contract_detail'),
    path('contracts/logout/', contract_logout_view, name='contract_logout'),
]
  