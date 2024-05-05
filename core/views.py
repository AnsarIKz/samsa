from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from datetime import datetime
from .models import Lesson, Profile, Event, ClubEvent
from datetime import timedelta
from .serializers import EventSerializer, ProfileSerializer
from django.shortcuts import get_object_or_404
import json


class CreateEventFromClubEvent(APIView):
    def post(self, request, club_event_id):
        # Получаем клубное событие
        club_event = get_object_or_404(ClubEvent, id=club_event_id)
        
        # Получаем user_id из payload
        user_id = request.data.get('user_id')
        
        # Проверяем, есть ли уже событие в это время
        existing_event = Event.objects.filter(
            start_time=club_event.start_time,
            name=club_event.name,
            description=club_event.description
        ).first()
        
        if existing_event:
            # Если событие уже существует, добавляем пользователя в участники
            existing_event.participants.add(user_id)
            existing_event.save()
            return Response({"message": "User added to existing event."}, status=status.HTTP_200_OK)
        
        # Создаем новое событие на основе клубного события
        new_event = Event.objects.create(
            name=club_event.name,
            description=club_event.description,
            start_time=club_event.start_time,
            type="CLUB"  # Нужно уточнить, какой тип события использовать
        )
        # Добавляем пользователя в участники нового события
        new_event.participants.add(user_id)
        new_event.save()
        
        return Response({"message": "Event created successfully."}, status=status.HTTP_201_CREATED)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Event

class ManageEventView(APIView):
    def put(self, request, event_id):
        # Получаем событие, которое хочет изменить пользователь
        event = get_object_or_404(Event, id=event_id)

        # Получаем user_id из payload
        user_id = request.data.get('user_id')

        # Проверяем, принадлежит ли событие пользователю
        if user_id != event.owner.id:
            return Response({"error": "You are not a participant of this event."}, status=status.HTTP_403_FORBIDDEN)

        # Получаем данные из запроса
        new_start_time = request.data.get('new_start_time')

        # Проверяем наличие данных в запросе
        if not new_start_time:
            return Response({"error": "New start time is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Обновляем время события
        event.start_time = new_start_time
        event.save()

        return Response({"message": "Event start time updated successfully."}, status=status.HTTP_200_OK)



class WeeklyEventsView(APIView):
    def post(self, request, date_str):
        try:
            # Преобразуем строку даты в объект datetime
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Получаем user_id из тела запроса
        try:
            payload = json.loads(request.body)
            user_id = payload.get('user_id')
            if user_id is None:
                raise ValueError()
        except (json.JSONDecodeError, ValueError):
            return Response({"error": "Invalid payload format. Include 'user_id'."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Вычисляем начало и конец недели относительно переданной даты
        start_of_week = date - timedelta(days=date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Получаем профиль пользователя или возвращаем 404, если не найден
        user_profile = get_object_or_404(Profile, id=user_id)
        
        if user_profile.is_teacher:
            weekly_events = user_profile.owned_events.filter(start_time__range=[start_of_week, end_of_week])
        else:
            weekly_events = user_profile.attended_events.filter(start_time__range=[start_of_week, end_of_week])

        
        # Сериализуем события и возвращаем их
        serializer = EventSerializer(weekly_events, many=True)
        return Response(serializer.data)
    def delete(self, request, event_id):
        # Получаем событие, которое хочет удалить пользователь
        event = get_object_or_404(Event, id=event_id)

        # Получаем user_id из payload
        user_id = request.data.get('user_id')

        # Проверяем, принадлежит ли событие пользователю
        if user_id != event.owner.id:
            return Response({"error": "You are not a participant of this event."}, status=status.HTTP_403_FORBIDDEN)

        # Удаляем событие
        event.delete()

        return Response({"message": "Event deleted successfully."}, status=status.HTTP_204_NO_CONTENT)






class CurrentUserView(APIView):
    def get(self, request):
        # Получаем user_id из payload
        user_id = request.data.get('user_id')

        # Получаем пользователя по user_id
        user = get_object_or_404(Profile, id=user_id)

        # Сериализуем данные пользователя
        serializer = ProfileSerializer(user)

        # Возвращаем данные пользователя в ответе
        return Response(serializer.data)




class GetLessonByTime(APIView):
    def post(self, request):
        # Получаем дату и время из Payload
        payload = request.data
        try:
            student_id = payload['student_id']
            lesson_datetime = datetime.strptime(payload['datetime'], '%Y-%m-%d %H:%M')
        except KeyError:
            return Response({'error': 'Datetime is required in payload'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Invalid datetime format. Use YYYY-MM-DD HH:MM'}, status=status.HTTP_400_BAD_REQUEST)

        try:    
            student_profile = Profile.objects.get(student_id=student_id)
        except Profile.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)

        # Получаем день недели
        weekday = lesson_datetime.strftime('%a').upper()

        # Получаем лекции и практики, которые проходят в указанное время и дату
        current_lesson = Lesson.objects.filter(course__in=student_profile.courses.all(), time=lesson_datetime.time(), weekday=weekday)

        # Формируем ответ
        response_data = {
            'student_id': student_id,
            'lesson_datetime': lesson_datetime.strftime('%Y-%m-%d %H:%M'),
            'current_lesson': [lesson.course.name for lesson in current_lesson],
        }


        return Response(response_data)


from rest_framework import generics
from .models import ClubEvent
from .serializers import ClubEventSerializer

class ClubEventListAPIView(generics.ListAPIView):
    queryset = ClubEvent.objects.all()
    serializer_class = ClubEventSerializer
