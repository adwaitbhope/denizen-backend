# Generated by Django 2.2.4 on 2019-10-25 20:44

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0033_auto_20191026_0029'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicevendor',
            name='township',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='backend.Township'),
        ),
        migrations.AlterField(
            model_name='securitypersonnel',
            name='shift_end',
            field=models.TimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='securitypersonnel',
            name='shift_start',
            field=models.TimeField(default=django.utils.timezone.now),
        ),
    ]
