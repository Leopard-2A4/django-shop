from rest_framework.views import APIView
from rest_framework.response import Response
from orders.models import Order
from shopproducts.serializers import TagSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse
from shopproducts.models import Tag


# Create your views here.

@extend_schema(tags=["Теги"])
class GetTagViewSet(APIView):

    @extend_schema(
        summary="Получить список тегов",
        description="Возвращает список всех активных (неархивированных) тегов",
        responses={
            200: OpenApiResponse(
                response=TagSerializer(many=True),
                description="Список тегов",)
        })
    def get(self, request):
        queryset = Tag.objects.filter(archived=False)
        return Response(TagSerializer(queryset, many=True).data)