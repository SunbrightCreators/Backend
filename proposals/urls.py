from django.urls import path
from .views import *

app_name = 'proposals'

urlpatterns = [
  path("", ProposalsRoot.as_view(), name="proposals-root"),
  path("<int:zoom>/", ProposalsZoom.as_view(), name="proposals-zoom"),
  path("<int:proposal_id>/<str:profile>/", ProposalsPk.as_view(), name="proposals-pk"),
  path("proposer/my-created", ProposalsMyCreated.as_view(), name="proposals-my-created"),
]

