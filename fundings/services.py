from django.http import HttpRequest
from utils.decorators import validate_data, validate_permission, validate_unique
from .models import ProposerLikeFunding, ProposerScrapFunding, FounderScrapFunding

class ProposerLikeFundingService:
    def __init__(self, request:HttpRequest):
        self.request = request

    def post(self, funding_id:int) -> bool:
        '''
        Args:
            funding_id (int): 펀딩 id
        Returns:
            is_created (bool):
                - `True`: 좋아요 추가
                - `False`: 좋아요 삭제
        '''
        obj, created = ProposerLikeFunding.objects.get_or_create(
            user__user=self.request.user,
            funding=funding_id,
        )
        if created:
            return True
        else:
            obj.delete()
            return False

class ProposerScrapFundingService:
    def __init__(self, request:HttpRequest):
        self.request = request

    def post(self, funding_id:int) -> bool:
        '''
        Args:
            funding_id (int): 펀딩 id
        Returns:
            is_created (bool):
                - `True`: 스크랩 추가
                - `False`: 스크랩 삭제
        '''
        obj, created = ProposerScrapFunding.objects.get_or_create(
            user__user=self.request.user,
            funding=funding_id,
        )
        if created:
            return True
        else:
            obj.delete()
            return False

class FounderScrapFundingService:
    def __init__(self, request:HttpRequest):
        self.request = request

    def post(self, funding_id:int) -> bool:
        '''
        Args:
            funding_id (int): 펀딩 id
        Returns:
            is_created (bool):
                - `True`: 스크랩 추가
                - `False`: 스크랩 삭제
        '''
        obj, created = FounderScrapFunding.objects.get_or_create(
            user__user=self.request.user,
            funding=funding_id,
        )
        if created:
            return True
        else:
            obj.delete()
            return False
