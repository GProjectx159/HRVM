# Generated by Django 5.0.3 on 2024-04-16 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_alter_vacation_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacation',
            name='substitute_employee',
            field=models.CharField(blank=True, default='', max_length=100, null=True),
        ),
    ]