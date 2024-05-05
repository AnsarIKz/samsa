
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    CreateEventFromClubEvent,
    ManageEventView,
    WeeklyEventsView,
    CurrentUserView,
    ClubEventListAPIView,
)

urlpatterns = [
    path('event/accept/<int:club_event_id>/', CreateEventFromClubEvent.as_view(), name='create_event_from_club_event'),
    path('event/change-time/<int:event_id>/', ManageEventView.as_view(), name='manage_event'),
    path('event/my/<str:date_str>/', WeeklyEventsView.as_view(), name='weekly_events'),
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('event/club-all/', ClubEventListAPIView.as_view(), name='club-event-list'),
    # path('search_users/', SearchUsersView.as_view(), name='search_users'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Получение токена доступа
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Обновление токена доступа
    
]
