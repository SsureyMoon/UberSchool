from django.conf.urls import url, include
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token

from .views import CustomObtainJSONWebToken, CustomRefreshJSONWebToken


urlpatterns = [
    url(r'token-auth/', CustomObtainJSONWebToken.as_view()),
    url(r'token-refresh/', CustomRefreshJSONWebToken.as_view()),
    url(r'auth/', include('rest_framework.urls', namespace='rest_framework'))
]