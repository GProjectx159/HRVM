from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.decorators import login_required
from .forms import MyUserCreationForm
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login as auth_login
from .models import User, DepartmentManager, Vacation, Notification
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.conf import settings
from django.db.models import Q, Max, F
from datetime import datetime, timedelta

from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.http import HttpResponseRedirect

from django.http import HttpResponse

import os

import base64
import pdfcrowd

def home(request):
 if request.user.is_authenticated:
        return redirect('home_after')
 return render(request, "home.html", {})

def error_404_view(request, exception):
    return render(request, '404.html')


class CustomPasswordResetView(PasswordResetView):
    form_class = PasswordResetForm
    template_name = 'registration/reset_password.html'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            context = {
                'user': user,
                'protocol': 'http',
                'domain': self.request.get_host(),
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            }
            html_message = render_to_string('registration/password_reset_email.html', context)
            plain_message = strip_tags(html_message)
            send_mail(
                'Password Reset Request',
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
            )
        else:
            message_error = "لا يمكننا العثور على البريد الإلكتروني الخاص بك."
            return render(self.request, 'registration/reset_password.html', {'message_error': message_error, 'email': email})

        return HttpResponseRedirect(self.get_success_url())
    
@login_required(login_url='login')
def home_after(request):
 return render(request, "home_after.html")


def loginUser(request):
    form = None
    if request.user.is_authenticated:
        return redirect('home_after')

    error_message = None

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user is not None and user.is_active: 
            user = authenticate(request, email=email, password=password)

            if user is not None:
                
                auth_login(request, user)
                return redirect('home_after')
            else:
                error_message = 'اسم المستخدم او كلمة المرور خطأ'
                submitted_data = request.POST.copy() 
                form = MyUserCreationForm(submitted_data)

        elif user is not None and not user.is_active:
            error_message = 'حسابك لم ينشط بعد اتصل بالدعم'
            submitted_data = request.POST.copy() 
            form = MyUserCreationForm(submitted_data)

        else:
            error_message = 'اسم المستخدم او كلمة المرور خطأ'
            submitted_data = request.POST.copy() 
            form = MyUserCreationForm(submitted_data)

    return render(request, 'registration/login.html', {'form':form , 'error_message': error_message})

def sginup(request):
    error_messages = None
    
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            employee_identity = form.cleaned_data.get('employee_identity')
            info = extract_info_from_national_id(employee_identity)
         
            user.birthdate = info['date_of_birth']
            user.gender = info['gender']
            user.save()
            return redirect("login")
        else:
            error_messages = form.errors
            submitted_data = request.POST.copy() 
            form = MyUserCreationForm(submitted_data)
    else:
        form = MyUserCreationForm()
    
    return render(request, "registration/signup.html", {"form": form, "error_messages": error_messages})

fake_national_id_message = 'This ID Not Valid'

def extract_birth_century(birth_century_code: int) -> int:

    assert type(birth_century_code) == int, 'birth century code must be int value'
    current_century = get_century_from_year(int(datetime.now().year))
    birth_century = birth_century_code + 18
    assert (birth_century >= 19) and (birth_century <= current_century), fake_national_id_message
    return birth_century


def get_century_from_year(year):
    return year // 100 + 1

def get_gender(gender_code: int) -> str:

    assert type(gender_code) == int and gender_code > 0 and gender_code <= 9, 'gender code not valid'
    if gender_code % 2 == 0:
        return 'Female'
    else:
        return 'Male'

def convert_birthdate(birthdate: str) -> str:

    assert len(str(birthdate)) == 7, "birthdate must be 7 digit"
    birth_century = extract_birth_century(int(birthdate[0]))
    birth_year = birthdate[1:3]
    birth_month = birthdate[3:5]
    birth_day = birthdate[5:]
    birth_full_year = (birth_century * 100) - 100 + int(birth_year)
    birthdate_str = '{0}-{1}-{2}'.format(birth_full_year, birth_month, birth_day)
    birthdate_date = datetime.strptime(birthdate_str, '%Y-%m-%d')
    assert birthdate_date <= datetime.now() and birthdate_date >= datetime.strptime('1900-01-01','%Y-%m-%d'), fake_national_id_message
    return birthdate_str

def extract_info_from_national_id(national_id: int):

    assert type(national_id) == int, "National ID must be Numbers not string"
    assert len(str(national_id)) == 14, "National ID must be 14 Number "
    national_id_str = str(national_id)
    info = {}
    info['date_of_birth'] = convert_birthdate(national_id_str[0:7])
    info['gender'] = get_gender(int(national_id_str[12]))
    return info


def logoutUser(request):
    logout(request)
    return redirect("home")

@login_required(login_url='login')
def userprofile(request, username):
    user = User.objects.get(username=username)
    if request.method == 'POST':
        new_address = request.POST.get('address')
        new_phone = request.POST.get('phone')
        user.address = new_address
        user.phone = new_phone
        user.save()
        
        if 'newSignature' in request.FILES:
            new_signature = request.FILES['newSignature']
            try:
                manager = DepartmentManager.objects.get(department=user.department)
                manager.signature = new_signature
                manager.save()
            except DepartmentManager.DoesNotExist:
                pass

            return redirect('user-profile', username=username)
        
    try:
        manager = DepartmentManager.objects.get(department=user.department)
    except DepartmentManager.DoesNotExist:
        manager = None
        
    context = {
        'user': user,
        'manager': manager,
    }
    return render(request, "profile.html", context)

@login_required(login_url='login')
def usersRequests(request):
    inactive_users = User.objects.filter(is_active=False)
    context = {
        'inactive_users' : inactive_users,
    }
    if not request.user.is_superuser:
        return render(request, "home_after.html", context)
    return render(request, "usersRequests.html", context)

def acceptUsers(request, username):
    user = User.objects.get(username=username)
    context = {
        'user' : user
    }
    return render(request, "acceptUsers.html", context)

def deleteUser(request, username):
    user = User.objects.get(username=username)
    user.delete()

    return usersRequests(request)

def updateUser(request, username):
    user = User.objects.get(username=username)
    is_superuser = request.POST.get('is_superuser')

    if is_superuser:
        user.is_superuser = True
        manager = DepartmentManager (
            employee = user,
            department = user.department
        )
        manager.save()
    else:
        user.is_superuser = False
        
    user.is_active = True
    user.save()
    
    return usersRequests(request)



def requestView(request):
    user = User.objects.get(username=request.user.username)
    allowed_user = User.objects.filter(department=user.department).exclude(pk=user.pk)
    # New ----------------------------------------
    q = request.GET.get('q')

    if request.user.department.department_id == 1:
        vacations = Vacation.objects.all()
    elif request.user.is_superuser:
        vacations = Vacation.objects.filter(employee__department=request.user.department)
    else:
        vacations = Vacation.objects.filter(employee=request.user)

    if q:
        vacations = vacations.filter(status=q)
    
    # ----------------------------------------
    end_date_requested = datetime.now().date() + timedelta(days=10)

    busy_alternates_ids = Vacation.objects.filter(
        Q(employee__in=allowed_user),
        Q(start_date__lte=end_date_requested, end_date__gte=datetime.now().date()) |
        Q(start_date__gte=datetime.now().date(), end_date__lte=end_date_requested) |
        Q(start_date__lte=datetime.now().date(), end_date__gte=datetime.now().date()) |
        Q(start_date__lte=end_date_requested, end_date__gte=end_date_requested)
    ).values_list('employee_id', flat=True)

    allowed_user = allowed_user.exclude(id__in=busy_alternates_ids)
    
    difference = datetime.now().date() - user.startwork_date.date()
    
    if difference.days >= 365:  
        if user.vacation1 == 15:
            user.vacation1 = 21
            user.vacation1_balance += 6  
            # if user.age > 50:
            #     user.vacation1 = 30
            user.save()

    context = {
        'user': user,
        'allowed_user': allowed_user,
        'vacations' : vacations,
        'department' : request.user.department
    }
    return render(request, "requestView.html", context)


def saveRequest(request):
    if request.method == 'POST':
        vacation_type = request.POST.get('vacation_type')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        description = request.POST.get('description')
        attachment = request.FILES.get('attachment')  # Use request.FILES for file uploads
        substitute_employee = request.POST.get('substitute_employee')  

        # Convert strings to datetime objects
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        # Get the maximum request_number
        max_request_number = Vacation.objects.aggregate(Max('request_number'))['request_number__max']

        if max_request_number is None:
            max_request_number = 0

        request_number = max_request_number + 1

        duration = end_date - start_date

        leave_request = Vacation(
            status=0,
            request_date=datetime.now().date(),
            request_number=request_number,
            start_date=start_date,
            end_date=end_date,
            duration=duration.days,
            employee=request.user,
            substitute_employee=substitute_employee,
            vacation_type=vacation_type,
            attachment=attachment,
            description=description
        )
        leave_request.save()

        user = User.objects.get(username=request.user.username)

        if vacation_type == '0':
            user.vacation1_balance = F('vacation1_balance') - duration.days
        elif vacation_type == '1':
            user.vacation2_balance = F('vacation2_balance') - duration.days
        elif vacation_type == '2':
            user.vacation3_balance = F('vacation3_balance') - duration.days
        elif vacation_type == '3':
            user.vacation4_balance = F('vacation4_balance') - 1

        user.save()

        # Create a notification for the user about the new vacation request
        message = f"تم إرسال طلب إجازة جديد: رقم الطلب {request_number}"
        Notification.objects.create(user=request.user, message=message)

    return redirect('requestView')


def AcceptRequest(request):
    manager_department = request.user.department
    employees = User.objects.filter(department=manager_department)
    vacations = Vacation.objects.filter(employee__in=employees, status='0')

    q = request.GET.get('q', '')
    if q:
        vacations = vacations.filter(
            Q(employee__name__icontains=q) |
            Q(request_number__icontains=q)
        )

    context = {
        'vacations': vacations,
    }
    return render(request, "AcceptRequest.html", context)


def showRequest(request, pk):
    vacation = Vacation.objects.get(request_number=pk)
    
    context = {
        'vacation': vacation,
    }
    return render(request, "showRequest.html", context)

def showMyRequest(request, pk):
    vacation = Vacation.objects.get(request_number=pk)
    
    context = {
        'vacation': vacation,
    }
    return render(request, "showMyRequest.html", context)

def approve_vacation(request, request_number):
    try:
        vacation = Vacation.objects.get(request_number=request_number)
        vacation.status = 2  
        manager_signature = DepartmentManager.objects.get(department=vacation.employee.department).signature
        vacation.manager_signature = manager_signature
        vacation.save()

        return redirect('AcceptRequest')
    except Vacation.DoesNotExist:
        return render(request, '404.html')

def reject_vacation(request, request_number):
    try:
        vacation = Vacation.objects.get(request_number=request_number)
        vacation.status = 1
        vacation.save()
        return redirect('AcceptRequest')
    except Vacation.DoesNotExist:
        return render(request, '404.html')


def pdf_report_create(request, request_number):
    template_path = 'pdf_template.html'

    # افترض أن اسم الصورة هو 'NCTU-logo-1 (1) (1).png' في مجلد media/base/images
    logo_path = os.path.join(settings.MEDIA_ROOT, 'NCTU-logo-1 (2).png')
    with open(logo_path, 'rb') as image_file:
        image_data = image_file.read()
    # Encode the image data to base64
    logo = base64.b64encode(image_data).decode('utf-8')

    vacation = Vacation.objects.get(request_number=request_number)

    manager_signature_path = os.path.join(settings.MEDIA_ROOT, f'{vacation.manager_signature}') 
    with open(manager_signature_path, 'rb') as image_file:
        image_data = image_file.read()
    # Encode the image data to base64
    manager_signature = base64.b64encode(image_data).decode('utf-8')

    data = {
        "vacation": vacation,
        "department": vacation.employee.department.name,
        "logo": logo,  # Pass the base64 string to the template
        "manager_signature": manager_signature,  # Pass the base64 string to the template
    }

    context = {'data': data}

    html_string = render_to_string(template_path, context)

    try:
        # Replace 'Gprojectx159' and '9169456ae59c510b81bc2bd5f3aa19e6' with your PDFCrowd username and API key
        client = pdfcrowd.HtmlToPdfClient('eslamx144', 'fa2c8229a1c90cc353bafd3cb53deddb')
        
        # Convert HTML string to PDF and save it to a file named "Vacation_report.pdf"
        client.convertStringToFile(html_string, 'Vacation_report.pdf')

        # Read the generated PDF file
        with open('Vacation_report.pdf', 'rb') as pdf_file:
            pdf = pdf_file.read()
        
        # Set response content type
        response = HttpResponse(pdf, content_type='application/pdf')
        return response

    except pdfcrowd.Error as why:
        # In case of error, return error message
        return HttpResponse("PDF conversion failed: {}".format(why))

    
