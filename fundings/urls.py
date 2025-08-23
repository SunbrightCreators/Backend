from django.urls import path
from .views import *

app_name = 'fundings'

urlpatterns = [
    path('proposer/like', ProposerLike.as_view()),
    path('<str:profile>/scrap', ProfileScrap.as_view()),
    path('<str:profile>/<int:zoom>', FundingMapView.as_view(), name='funding-map'),
    path('<int:funding_id>/<str:profile>', FundingDetailView.as_view(), name='funding-detail'),
    path('founder/my-created', FounderMyCreatedView.as_view(), name='funding-my-created'),
]