# Generated by Django 5.0.4 on 2024-05-05 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_rename_member_event_participants'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='location',
            field=models.CharField(default=1, max_length=200),
            preserve_default=False,
        ),
    ]
