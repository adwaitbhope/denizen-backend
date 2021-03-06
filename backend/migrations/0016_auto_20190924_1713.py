# Generated by Django 2.2.4 on 2019-09-24 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0015_township_verification_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='reset_password_link',
            field=models.CharField(blank=True, default=None, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='reset_password_request_timestamp',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
