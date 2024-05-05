from rest_framework import serializers
from .models import Event, ClubEvent

class EventSerializer(serializers.ModelSerializer):
    weekday = serializers.SerializerMethodField()

    def get_weekday(self, obj):
        # Получаем день недели из start_time события и возвращаем его как число от 1 до 7
        if obj.start_time:
            return obj.start_time.isoweekday()  # Возвращает число от 1 (понедельник) до 7 (воскресенье)
        else:
            return None  # Возвращаем None, если start_time отсутствует

    class Meta:
        model = Event
        fields = ['owner', 'name', 'description', 'location', 'start_time', 'type', 'weekday']


from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'email', 'is_active', 'is_staff', 'date_joined', 'student_id', 'year_of_entry', 'full_name', 'faculty', 'adviser', 'birth_date', 'status', 'is_teacher']


from rest_framework import serializers
from .models import ClubEvent

class ClubEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClubEvent
        fields = ['id', 'name', 'description', 'start_time', 'img']
