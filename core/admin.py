from django.contrib import admin
from .models import Lesson, Profile, Event, ClubEvent

# Register your models here.
admin.site.register(Lesson)
admin.site.register(Profile)
admin.site.register(Event)
admin.site.register(ClubEvent)