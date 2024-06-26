# Generated by Django 5.0.4 on 2024-04-13 12:29

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('department_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(default='', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('is_active', models.BooleanField(default=False)),
                ('employee_identity', models.BigIntegerField(default=0, unique=True)),
                ('name', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('email', models.EmailField(max_length=254, null=True, unique=True)),
                ('phone', models.CharField(blank=True, max_length=50, null=True)),
                ('startwork_date', models.DateTimeField(blank=True, null=True)),
                ('birthdate', models.DateField(blank=True, null=True)),
                ('address', models.CharField(blank=True, default='', max_length=1000, null=True)),
                ('gender', models.CharField(default='', max_length=10)),
                ('vacation1', models.IntegerField(default=15)),
                ('vacation1_balance', models.IntegerField(default=15)),
                ('vacation2_balance', models.IntegerField(default=7)),
                ('vacation3_balance', models.IntegerField(default=10)),
                ('vacation4_balance', models.IntegerField(default=2)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='base.department')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('is_read', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Vacation',
            fields=[
                ('vacation_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('0', 'Pending'), ('1', 'Refused'), ('2', 'Accepted')], max_length=10)),
                ('request_date', models.DateTimeField()),
                ('request_number', models.BigIntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('duration', models.PositiveIntegerField()),
                ('vacation_type', models.CharField(choices=[('0', 'اجازه اعتياديه'), ('1', 'اجازه عارضه'), ('2', 'اجازه مرضيه'), ('3', 'اجازه وضع'), ('4', 'اذن'), ('5', 'مأموريه')], max_length=10)),
                ('attachment', models.ImageField(blank=True, null=True, upload_to='images/')),
                ('description', models.CharField(blank=True, default='', max_length=1000, null=True)),
                ('manager_signature', models.ImageField(blank=True, null=True, upload_to='')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DepartmentManager',
            fields=[
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('signature', models.ImageField(null=True, upload_to='')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.department')),
            ],
        ),
    ]
