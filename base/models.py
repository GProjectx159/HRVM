from django.db import models
from django.contrib.auth.models import AbstractUser


class Department(models.Model):
    department_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, default='')

    def __str__(self):
        return self.name

class User(AbstractUser):
    is_active = models.BooleanField(default=False)
    employee_identity = models.BigIntegerField(unique=True,default=0)
    name = models.CharField(max_length=100, default='', blank=True, null=True)
    email = models.EmailField(unique=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    startwork_date = models.DateTimeField(blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True)
    address = models.CharField(max_length=1000, default='', blank=True, null=True)
    gender = models.CharField(max_length=10, default='')

    vacation1 = models.IntegerField(default=0) 
    vacation1_balance = models.IntegerField(default=0) #اجازه اعتياديه
    vacation2_balance = models.IntegerField(default=7) #اجازه عارضه
    vacation3_balance = models.IntegerField(default=10) #اجازه مرضيه
    vacation4_balance = models.IntegerField(default=2) #اجازه وضع

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.name if self.name else "No name"


class Vacation(models.Model):
    vacation_id = models.BigAutoField(primary_key=True)
    STATUS_CHOICES = (
        ('0', 'مُعلق'),
        ('1', 'تم الرفض'),
        ('2', 'تم الوافقة'),
    )
    VACATION_TYPE_CHOICES = (
        ('0', 'اجازه اعتياديه'),
        ('1', 'اجازه عارضه'),
        ('2', 'اجازه مرضيه'),
        ('3', 'اجازه وضع'),
        ('4', 'اذن'),
        ('5', 'مأموريه'),
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    request_date = models.DateTimeField()
    request_number = models.BigIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.PositiveIntegerField()
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    vacation_type = models.CharField(max_length=10, choices=VACATION_TYPE_CHOICES)
    attachment = models.ImageField(null=True, blank=True, upload_to="images/")
    description = models.CharField(max_length=1000, default='', blank=True, null=True)

    substitute_employee = models.CharField(max_length=100, default='', blank=True, null=True)
    manager_signature = models.ImageField(null=True, blank=True)


    def save(self, *args, **kwargs):
        # Calculate duration before saving
        self.duration = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)
        
    def __str__(self):
        return str(self.request_number)

class DepartmentManager(models.Model):
    employee = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    signature = models.ImageField(null=True)

    def __str__(self):
        return str(self.department.name)
    