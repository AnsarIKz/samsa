from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin



WEEKDAYS = (
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    )

EVENT_TYPES = (
    ('LESSON', 'Lesson'),
    ('CLUB', 'Club'),
    ('CUSTOM', 'Custom'),
    ('OFFICE', 'Office hours'),
)
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class Profile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    student_id = models.CharField(max_length=20)
    year_of_entry = models.PositiveSmallIntegerField(default=timezone.now().year)
    full_name = models.CharField(max_length=100, null=True)
    faculty = models.CharField(max_length=100, null=True)
    adviser = models.CharField(max_length=100, null=True)
    birth_date = models.DateField(null=True)
    status = models.CharField(max_length=20, null=True)
    is_teacher = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['student_id']  # Add any additional required fields here

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class ClubEvent(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    start_time = models.DateTimeField()
    img = models.ImageField(upload_to='club_event_images/', null=True, blank=True)  

class Event(models.Model):
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='owned_events')
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    location = models.CharField(max_length=200, null=True)
    start_time = models.DateTimeField(null=True)
    participants = models.ManyToManyField(Profile, related_name='attended_events')  
    type = models.CharField(max_length=10, choices=EVENT_TYPES, default='LESSON')

# class Course(models.Model):

class Lesson(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='taught_lessons')
    time = models.TimeField()
    location = models.CharField(max_length=200)
    weekday = models.CharField(max_length=3, choices=WEEKDAYS)
    participants = models.ManyToManyField(Profile, related_name='attended_lessons')
    type = models.CharField(max_length=3, choices=(('LCT', 'Lecture'), ('PRC','Practice'), ('OFH', 'Office Hours')))

    def __str__(self):
        return f"Lesson: {self.name} at {self.time} on {self.weekday}"

    
# class Practice(models.Model):
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     time = models.TimeField()
#     location = models.CharField(max_length=200)
#     weekday = models.CharField(max_length=3, choices=WEEKDAYS)
#     participants = models.ManyToManyField(Profile)  

#     def __str__(self):
#         return f"Practice for {self.course.name} at {self.time}"

# class Lecture(models.Model):
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     time = models.TimeField()
#     location = models.CharField(max_length=200)
#     weekday = models.CharField(max_length=3, choices=WEEKDAYS)
#     participants = models.ManyToManyField(Profile)  

#     def __str__(self):
#         return f"Lecture for {self.course.name} at {self.time}"

# class OfficeHours(models.Model):
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     time = models.TimeField()
#     location = models.CharField(max_length=200)
#     weekday = models.CharField(max_length=3, choices=WEEKDAYS)

#     def __str__(self):
#         return f"Office Hours for {self.course.name}"

    
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
import requests
from django.core.exceptions import ObjectDoesNotExist
from collections import defaultdict

def isProfileBusyInTime(participant, current_slot):
    # Проверяем, есть ли у профиля лекция в указанное время
    if Lesson.objects.filter(participants=participant, time=current_slot.time()).exists():
        return True
    
    return False


def calculate_semester_start_date():
    current_date = datetime.now()
    current_year = current_date.year
    first_september = datetime(current_year, 9, 1)
    first_september_weekday = first_september.weekday()
    days_until_monday = (7 - first_september_weekday) % 7
    semester_start_date = first_september + timedelta(days=days_until_monday)

    return semester_start_date

def is_holiday(date):
    url = f"https://isdayoff.ru/{date.strftime('%Y%m%d')}?cc=KZ"
    response = requests.get(url)
    return response.json() == 1

def find_best_slot(event_date, participants):
    slots_count = defaultdict(int)

    for i in range(3):
        current_date = event_date + timedelta(days=i)

        for hour in range(8, 18):
            current_slot = timezone.datetime(current_date.year, current_date.month, current_date.day, hour)
            for participant in participants:
                if not isProfileBusyInTime(participant, current_slot):
                    slots_count[hour] += 1  # Увеличиваем количество свободных участников

    best_slot = max(slots_count, key=slots_count.get)

    return best_slot

def is_weekend(date):
    return date.weekday() == 6  # Проверяем, является ли день субботой (5) или воскресеньем (6)


@receiver(m2m_changed, sender=Lesson.participants.through)
def create_events(sender, instance, action, **kwargs):
    if action == "post_add":
        semester_start_date = timezone.datetime(timezone.now().year, 1, 20)
        semester_weeks = 15

        # Определяем день недели, на который должны создаваться события
        weekday_mapping = {
            'MON': 0,
            'TUE': 1,
            'WED': 2,
            'THU': 3,
            'FRI': 4,
            'SAT': 5,
            'SUN': 6,
        }
        weekday_number = weekday_mapping.get(instance.weekday)

        # Создаем события для каждой недели семестра
        for week in range(semester_weeks):
            # Вычисляем дату события для текущей недели
            event_date = semester_start_date + timedelta(weeks=week, days=(weekday_number - 1))

            # Если дата является выходным днем или праздничным днем, пропустить создание события
            if is_weekend(event_date) or is_holiday(event_date):
                continue

            # Найти лучшее время для события и создать его
            best_slot = find_best_slot(event_date, instance.participants.all())
            event_time = instance.time.replace(hour=best_slot)
            event_location = instance.location

            event = Event.objects.create(
                owner=instance.teacher,
                location=event_location,
                name=f"{instance.__class__.__name__} for {instance.name}",
                description=f"{instance.__class__.__name__} for {instance.name} at {event_time} on {event_date}",
                start_time=event_date,
            )
            event.participants.add(*instance.participants.all())


                # if not Event.objects.filter(start_time__date=event_date.date(), participants=participant).exists():
                #     similar_lesson = Lesson.objects.filter(
                #         name=instance.name,
                #         type=instance.type,
                #         start_time__gte=event_date,
                #     ).exclude(pk=instance.pk).order_by('start_time').first()

                #     if similar_lesson:
                #         if not similar_lesson.participants.filter(pk=participant.pk).exists():
                #             similar_lesson.participants.add(participant)