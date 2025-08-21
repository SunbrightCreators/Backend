from django.http import HttpRequest
from django.db.models import Count, Sum
from utils.decorators import validate_data, validate_permission, validate_unique
from .models import Proposal, ProposerLikeProposal, ProposerScrapProposal, FounderScrapProposal
from .serializers import ProposalListSerializer

class ProposerLikeProposalService:
    def __init__(self, request:HttpRequest):
        self.request = request

    def post(self, proposal_id:int) -> bool:
        '''
        Args:
            proposal_id (int): 제안 id
        Returns:
            is_created (bool):
                - `True`: 좋아요 추가
                - `False`: 좋아요 삭제
        '''
        obj, created = ProposerLikeProposal.objects.get_or_create(
            user__user=self.request.user,
            proposal=proposal_id,
        )
        if created:
            return True
        else:
            obj.delete()
            return False

class ProposerScrapProposalService:
    def __init__(self, request:HttpRequest):
        self.request = request

    def post(self, proposal_id:int) -> bool:
        '''
        Args:
            proposal_id (int): 제안 id
        Returns:
            is_created (bool):
                - `True`: 스크랩 추가
                - `False`: 스크랩 삭제
        '''
        obj, created = ProposerScrapProposal.objects.get_or_create(
            user__user=self.request.user,
            proposal=proposal_id,
        )
        if created:
            return True
        else:
            obj.delete()
            return False

    def get(self, sido:str|None=None, sigungu:str|None=None, eupmyundong:str|None=None):
        proposals = Proposal.objects.filter(
            proposer_scrap_proposal__user__user=self.request.user,
            address__sido=sido,
            address__sigungu=sigungu,
            address__eupmyundong=eupmyundong,
        ).annotate(
            likes_count=Count('proposer_like_proposal'),
            scraps_count=Count('proposer_scrap_proposal')+Count('founder_scrap_proposal'),
        ).select_related(
            'user__user',
        )
        serializer = ProposalListSerializer(proposals)
        return serializer.data

class FounderScrapProposalService:
    def __init__(self, request:HttpRequest):
        self.request = request

    def post(self, proposal_id:int) -> bool:
        '''
        Args:
            proposal_id (int): 제안 id
        Returns:
            is_created (bool):
                - `True`: 스크랩 추가
                - `False`: 스크랩 삭제
        '''
        obj, created = FounderScrapProposal.objects.get_or_create(
            user__user=self.request.user,
            proposal=proposal_id,
        )
        if created:
            return True
        else:
            obj.delete()
            return False

    def get(self, sido:str|None=None, sigungu:str|None=None, eupmyundong:str|None=None):
        proposals = Proposal.objects.filter(
            founder_scrap_proposal__user__user=self.request.user,
            address__sido=sido,
            address__sigungu=sigungu,
            address__eupmyundong=eupmyundong,
        ).annotate(
            likes_count=Count('proposer_like_proposal'),
            scraps_count=Count('proposer_scrap_proposal')+Count('founder_scrap_proposal'),
        ).select_related(
            'user__user',
        )
        serializer = ProposalListSerializer(proposals)
        return serializer.data
