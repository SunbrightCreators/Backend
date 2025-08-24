from django.http import HttpRequest
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from utils.decorators import validate_path_choices
from utils.helpers import resolve_viewer_addr

from utils.choices import ProfileChoices, ZoomChoices, FundingStatusChoices
from maps.services import GeocodingService
from .serializers import FundingIdSerializer, FundingMapSerializer
from .models import Funding
from .services import (
    ProposerLikeFundingService, 
    ProposerScrapFundingService, 
    FounderScrapFundingService, 
    FundingMapService, 
    FundingDetailService,
    FounderMyCreatedFundingService,
    ProposerMyPaidFundingService,
    ProposerMyRewardsService
)

class ProposerLike(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request:HttpRequest, format=None):
        serializer = FundingIdSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        funding_id = serializer.validated_data['funding_id']

        service = ProposerLikeFundingService(request)
        is_created = service.post(funding_id)

        if is_created:
            return Response(
                { 'detail': '이 펀딩을 좋아해요.' },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                { 'detail': '좋아요를 취소했어요.' },
                status=status.HTTP_200_OK,
            )

@method_decorator(validate_path_choices(profile=ProfileChoices.values), name='dispatch')
class ProfileScrap(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request:HttpRequest, profile, format=None):
        serializer = FundingIdSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        funding_id = serializer.validated_data['funding_id']

        if profile == ProfileChoices.proposer.value:
            service = ProposerScrapFundingService(request)
        elif profile == ProfileChoices.founder.value:
            service = FounderScrapFundingService(request)
        is_created = service.post(funding_id)

        if is_created:
            return Response(
                { 'detail': '이 펀딩을 스크랩했어요.' },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                { 'detail': '스크랩을 취소했어요.' },
                status=status.HTTP_200_OK,
            )

    def get(self, request:HttpRequest, profile, format=None):
        sido = request.query_params.get('sido')
        sigungu = request.query_params.get('sigungu')
        eupmyundong = request.query_params.get('eupmyundong')

        if profile == ProfileChoices.proposer.value:
            service = ProposerScrapFundingService(request)
        elif profile == ProfileChoices.founder.value:
            service = FounderScrapFundingService(request)
        data = service.get(sido, sigungu, eupmyundong)

        return Response(
            data,
            status=status.HTTP_200_OK,
        )
    
@method_decorator(validate_path_choices(profile=ProfileChoices.values), name='dispatch')
class FundingMapView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request: HttpRequest, profile: str, zoom: int, *args, **kwargs):
        # --- 입력 ---
        sido        = request.query_params.get("sido")
        sigungu     = request.query_params.get("sigungu")
        eupmyundong = request.query_params.get("eupmyundong")
        industry    = request.query_params.get("industry")
        order       = request.query_params.get("order", "최신순")

        # --- 검증 ---
        if zoom not in ZoomChoices.values:
            return Response(
                {"detail": f"Invalid zoom. Use one of: {ZoomChoices.values}"}, 
                status=status.HTTP_400_BAD_REQUEST)
        if zoom == ZoomChoices.M2000 and not sido:
            return Response(
                {"detail": "구 지도(2km)에는 sido가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST)
        if zoom == ZoomChoices.M500 and not (sido and sigungu):
            return Response(
                {"detail": "동 지도(500m)에는 sido와 sigungu가 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST)
        if zoom == ZoomChoices.M0 and not (sido and sigungu and eupmyundong):
            return Response(
                {"detail": "sido, sigungu, eupmyundong 쿼리 파라미터가 모두 필요합니다."}, 
                status=status.HTTP_400_BAD_REQUEST)
    
        # 중심좌표(지오코딩)
        try:
            geocoder = GeocodingService(request)  # 시그니처가 request를 받는 경우
        except TypeError:
            geocoder = GeocodingService()

        viewer_addr = resolve_viewer_addr(request.user, profile)

         # 서비스 호출
        svc = FundingMapService(request)
        
        # 동 이하(0): 상세 리스트
        if zoom == ZoomChoices.M0:
            try:
                qs = (
                    Funding.objects
                    .filter_address(sido, sigungu, eupmyundong)
                    .filter(status=FundingStatusChoices.IN_PROGRESS)
                    .with_analytics()
                    .with_level_area(sido=sido, sigungu=sigungu, eupmyundong=eupmyundong)
                    .filter_industry_choice(industry)
                    .with_proposal()
                    .with_flags(user=request.user, profile=profile)
                    .order_by_choice(order)
                )
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            data = FundingMapSerializer(
                qs, many=True,
                context={
                    "request": request, 
                    "profile": profile, 
                    "geocoder": geocoder,
                    "viewer_addr": viewer_addr
                    }
            ).data
            # proposer: is_liked/is_scrapped, founder: is_scrapped만 (serializer에서 제거)
            return Response(data, status=status.HTTP_200_OK)

        # 클러스터(시도/시군구/읍면동)
        if zoom == ZoomChoices.M10000:
            grouped = svc.cluster_counts_sido(industry)
        elif zoom == ZoomChoices.M2000:
            grouped = svc.cluster_counts_sigungu(sido, industry)
        else:  # M500
            grouped = svc.cluster_counts_eupmyundong(sido, sigungu, industry)

        def _match(viewer, *, sido=None, sigungu=None, eup=None) -> bool:
            if not viewer:
                return False
            def _one(a: dict) -> bool:
                if not isinstance(a, dict): return False
                if sido and a.get("sido") != sido: return False
                if sigungu is not None and a.get("sigungu") != sigungu: return False
                if eup is not None and a.get("eupmyundong") != eup: return False
                return True
            if isinstance(viewer, list):
                return any(_one(a) for a in viewer)
            if isinstance(viewer, dict):
                return _one(viewer)
            return False
        

        result = []
        for idx, row in enumerate(grouped, start=1):
            addr_text = row["address"]
            if zoom == ZoomChoices.M10000:
                full_addr = addr_text
                is_addr = _match(viewer_addr, sido=addr_text)
            elif zoom == ZoomChoices.M2000:
                full_addr = f"{sido} {addr_text}"
                is_addr = _match(viewer_addr, sido=sido, sigungu=addr_text)
            else:
                full_addr = f"{sido} {sigungu} {addr_text}"
                is_addr = _match(viewer_addr, sido=sido, sigungu=sigungu, eup=addr_text)

            # position 반환
            try:
                pos = geocoder.get_address_to_position(query_address=full_addr)
            except Exception:
                pos = {"latitude": None, "longitude": None}

            result.append({
                "id": idx,
                "address": addr_text,
                "position": pos,
                "number": row["number"],
                "is_address": is_addr,

            })
        return Response(result, status=status.HTTP_200_OK)

    
@method_decorator(validate_path_choices(profile=ProfileChoices.values), name='dispatch')
class FundingDetailView(APIView):
    authentication_classes = [JWTAuthentication] 
    permission_classes = [IsAuthenticated]        

    def get(self, request: HttpRequest, funding_id: int, profile: str, *args, **kwargs):
        svc = FundingDetailService(request)
        profile = (profile or "").lower()
        if profile == ProfileChoices.proposer.value:
            data = svc.get_for_proposer(funding_id)   # ← 없으면 403
        elif profile == ProfileChoices.founder.value:
            data = svc.get_for_founder(funding_id)    # ← 없으면 403
        else:
            raise PermissionDenied("허용되지 않은 profile 입니다. (founder|proposer)")
        return Response(data, status=status.HTTP_200_OK)

    
class FounderMyCreatedView(APIView):
    """
    GET /fundings/founder/my-created
    현재 로그인한 Founder가 작성한 펀딩을 상태별(진행/성공/실패) 최신순으로 반환
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest, *args, **kwargs):
        svc = FounderMyCreatedFundingService(request)
        data = svc.get()
        return Response(data, status=200)
    

class ProposerMyPaidView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest, *args, **kwargs):
        svc = ProposerMyPaidFundingService(request)
        data = svc.get()
        return Response(data, status=status.HTTP_200_OK)
    
class ProposerMyRewardsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest, *args, **kwargs):
        category = request.query_params.get("category")  # LEVEL | GIFT | COUPON | None
        svc = ProposerMyRewardsService(request)
        try:
            data = svc.get(category)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)
