# Generated by Django 5.1 on 2024-09-04 13:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_alter_job_is_saved'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='is_saved',
        ),
    ]