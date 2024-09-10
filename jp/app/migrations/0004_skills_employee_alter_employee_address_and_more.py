# Generated by Django 5.1 on 2024-08-23 16:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_employee_resume'),
    ]

    operations = [
        migrations.AddField(
            model_name='skills',
            name='employee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.employee'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='address',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='city',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='date',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='phonenumber',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='pincode',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='state',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='employer',
            name='address',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='employer',
            name='city',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='employer',
            name='phonenumber',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='employer',
            name='pincode',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='employer',
            name='state',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
