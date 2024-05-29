from django.contrib.auth import logout, authenticate, login as auth_login
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.tokens import default_token_generator

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import HttpResponseRedirect
from django.http import HttpResponse

from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Q, Max, F
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from django.conf import settings
from .forms import MyUserCreationForm
from .models import User, DepartmentManager, Vacation, Department
from datetime import datetime, timedelta

import os
import base64
import pdfcrowd

def error_404_view(request, exception):
    return render(request, 'error_page/404.html')

def home(request):
    if request.user.is_authenticated:
            return redirect('home_after')
    return render(request, "main_page/home.html")

@login_required(login_url='login')
def home_after(request):
    return render(request, "main_page/home_after.html")

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
                if user.is_superuser:
                    return redirect('AcceptRequest')
                else:
                    return redirect('user-profile', username = request.user.username)
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
    
def signup(request):
    error_messages = None
    
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            
            try:
                validate_email(email)
            except ValidationError:
                error_messages = {'email': ['يرجى إدخال بريد إلكتروني صحيح.']}
                form = MyUserCreationForm(request.POST)
                return render(request, "registration/signup.html", {"form": form, "error_messages": error_messages})
            
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
        user.address = request.POST.get('address')
        user.phone = request.POST.get('phone')
        user.save()
        
        if 'newSignature' in request.FILES:
            try:
                manager = DepartmentManager.objects.get(department=user.department)
                manager.signature = request.FILES['newSignature']
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
    return render(request, "user/profile.html", context)

@login_required(login_url='login')
def usersRequests(request):
    inactive_users = User.objects.filter(is_active=False)
    context = {
        'inactive_users' : inactive_users,
    }
    if not request.user.is_superuser:
        return render(request, "main_page/home_after.html", context)
    return render(request, "controll/usersRequests.html", context)

@login_required(login_url='login')
def acceptUsers(request, username):
    user = User.objects.get(username=username)
    context = {
        'user' : user
    }
    return render(request, "controll/acceptUsers.html", context)

@login_required(login_url='login')
def deleteUser(request, username):
    user = User.objects.get(username=username)
    user.delete()
    return usersRequests(request)

@login_required(login_url='login')
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

@login_required(login_url='login')
def manageDepartment(request):
    departments = Department.objects.all()
    managers = DepartmentManager.objects.all()

    department_dict = {department.department_id: department for department in departments}
    manager_dict = {manager.department_id: manager for manager in managers}

    full_join_result = []

    for department_id, department in department_dict.items():
        manager = manager_dict.get(department_id)
        if manager:
            full_join_result.append((department, manager))
        else:
            full_join_result.append((department, None))

    for manager_id, manager in manager_dict.items():
        if manager_id not in department_dict:
            full_join_result.append((None, manager))


    """
        get the new department name and manager id

        add the departent in Departmen table and get the boject

        get the manager object
        create a new row in departmentManager table
        add the department and new manager

    """

    if request.method == 'POST':
        department_name = request.POST.get('department_name')
        department_manager_id = request.POST.get('department_manager')

        department = Department.objects.create(
            name = department_name
        )

        manager = User.objects.get(id = department_manager_id)
        manager.is_superuser = True
        manager.save()

        DepartmentManager.objects.create(
            employee = manager,
            department = department,
        )
        return redirect("manageDepartment")

    manager_list_ids = DepartmentManager.objects.values_list("employee__id")
    users = User.objects.all().exclude(id__in=manager_list_ids)
    context = {
        'full_join_result' : full_join_result,
        'users' : users,
    }
    
    return render(request, "controll/manageDepartment.html", context)


def editdepartment(request, department_id):

    """
        - first get the department
        - check if the department is in deparmentManager
            - if exist
                get the manager
                get the name
                update the manager in DepartmentManager
                update the departmen name in departments
            
            - if not exists
                create a new one in departmentManager
                with new employee and new 
    """
    department_manager = None

    curr_department = Department.objects.get(department_id=department_id)
    if request.method == 'POST':
        new_manager_id = request.POST.get('new_manager_id')
        new_department_name = request.POST.get('new_daprtment_name')
        curr_department.name = new_department_name
        curr_department.save()

        new_manager = User.objects.get(id=new_manager_id)
        if DepartmentManager.objects.filter(department=curr_department).exists():
            department_manager = DepartmentManager.objects.filter(department=curr_department)
            department_manager.update(employee = new_manager)
            
        else:
            department_manager = DepartmentManager.objects.create(
                employee = new_manager,
                department = curr_department
            )
            department_manager.save()
        
        new_manager.is_superuser = True
        new_manager.save()
        return redirect("manageDepartment")

    department_manager = DepartmentManager.objects.get(department=curr_department) if DepartmentManager.objects.filter(department=curr_department).exists() else None
    
    manager_list_ids = DepartmentManager.objects.values_list("employee__id")
    users = User.objects.all().exclude(id__in=manager_list_ids)
    context = {
        'curr_department' : curr_department,
        'department_manager' : department_manager,
        'users' : users,
        
    }

    return render(request, "controll/editdepartment.html", context)


def requestView(request):
    q = request.GET.get('q')

    if request.user.department.department_id == 1:
        vacations = Vacation.objects.filter(status=2).order_by('-request_number')
    elif request.user.is_superuser:
        vacations = Vacation.objects.filter(employee__department__department_id=request.user.department.department_id,status=2).order_by('-request_number')
    else:
        vacations = Vacation.objects.filter(employee=request.user).order_by('-request_number')

    if q:
        vacations = vacations.filter(status=q)

    context = {
        'vacations': vacations,
        'department': request.user.department
    }
    return render(request, "vacation_request/requestView.html", context)


def AcceptRequest(request):
    manager_department = request.user.department
    employees = User.objects.filter(department=manager_department)
    vacations = Vacation.objects.filter(employee__in=employees, status='0').order_by('-request_number')

    q = request.GET.get('q', '')
    if q:
        vacations = vacations.filter(
            Q(employee__name__icontains=q) |
            Q(request_number__icontains=q)
        )

    context = {
        'vacations': vacations,
    }
    return render(request, "vacation_request/AcceptRequest.html", context)

    
def vacationRequest(request):
    user = User.objects.get(username=request.user.username)
    allowed_user = User.objects.filter(department=user.department).exclude(pk=user.pk)
    error_message = None

    if request.method == 'POST':
        vacation_type = request.POST.get('vacation_type')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        description = request.POST.get('description')
        attachment = request.FILES.get('attachment')
        substitute_employee = request.POST.get('substitute_employee')  

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        previous_vacations = Vacation.objects.filter(employee=user, end_date__gte=start_date, start_date__lte=end_date).exclude(status=1)
        if previous_vacations.exists():
            error_message = "لقد تم بالفعل تقديم طلب إجازة في هذه الفترة"

        substitute_employee_data = User.objects.get(id=substitute_employee)

        sub_employee_vacations = Vacation.objects.filter(employee=substitute_employee_data)

        if sub_employee_vacations.filter(start_date__lte=start_date, end_date__gte=start_date).exists() \
                or sub_employee_vacations.filter(start_date__lte=end_date, end_date__gte=end_date).exists():
            error_message = "الموظف البديل غير متوفر في هذه الفترة"

        if not error_message:
            max_request_number = Vacation.objects.aggregate(Max('request_number'))['request_number__max']
            request_number = max_request_number + 1 if max_request_number is not None else 1
            duration = (end_date - start_date).days

            leave_request = Vacation(
                status=0,
                request_date=datetime.now().date(),
                request_number=request_number,
                start_date=start_date,
                end_date=end_date,
                duration=duration,
                employee=request.user,
                substitute_employee=substitute_employee_data.name,
                vacation_type=vacation_type,
                attachment=attachment,
                description=description
            )

            leave_request.save()

            if vacation_type == '0':
                user.vacation1_balance -= duration
            elif vacation_type == '1':
                user.vacation2_balance -= duration
            elif vacation_type == '2':
                user.vacation3_balance -= duration
            elif vacation_type == '3':
                user.vacation4_balance -= 1
                
            user.save()

            return redirect('requestView')

    context = {
        'user': user,
        'allowed_user': allowed_user,
        'error_message': error_message,
        'department': request.user.department
    }
    return render(request, "vacation_request/vacationRequest.html", context)


def showRequest(request, pk):
    vacation = Vacation.objects.get(request_number=pk)
    
    context = {
        'vacation': vacation,
    }
    return render(request, "vacation_request/showRequest.html", context)

def showMyRequest(request, pk):
    vacation = Vacation.objects.get(request_number=pk)
    
    context = {
        'vacation': vacation,
    }
    return render(request, "vacation_request/showMyRequest.html", context)

def approve_vacation(request, request_number):
    try:
        vacation = Vacation.objects.get(request_number=request_number)
        vacation.status = 2  
        manager_signature = DepartmentManager.objects.get(department=vacation.employee.department).signature
        vacation.manager_signature = manager_signature
        vacation.save()

        context = {
            'user': vacation.employee,
            'protocol': 'http',
            'domain': request.get_host(),
            'vacation_id': vacation.request_number,
        }
        html_message = render_to_string('notifications/acceptVacation.html', context)
        plain_message = strip_tags(html_message)
        send_mail(
            'Vacation Accepted',
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [vacation.employee.email],
            html_message=html_message,
        )
        return redirect('AcceptRequest')
    
    except Vacation.DoesNotExist:
        return render(request, 'error_page/404.html')


def reject_vacation(request, request_number):
    try:
        vacation = Vacation.objects.get(request_number=request_number)
        vacation.status = 1
        vacation.save()

        user = User.objects.get(id=vacation.employee.id)
        
        vacation_type = vacation.vacation_type
        duration = vacation.duration

        if vacation_type == '0':
            user.vacation1_balance = F('vacation1_balance') + duration
        elif vacation_type == '1':
            user.vacation2_balance = F('vacation2_balance') + duration
        elif vacation_type == '2':
            user.vacation3_balance = F('vacation3_balance') + duration
        elif vacation_type == '3':
            user.vacation4_balance = F('vacation4_balance') + 1

        user.save()


        context = {
            'user': vacation.employee,
            'protocol': 'http',
            'domain': request.get_host(),
            'vacation_id': vacation.request_number,
        }
        html_message = render_to_string('notifications/rejectVacation.html', context)
        plain_message = strip_tags(html_message)
        send_mail(
            'Vacation Rejected',
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [vacation.employee.email],
            html_message=html_message,
        )

        return redirect('AcceptRequest')
    except Vacation.DoesNotExist:
        return render(request, 'error_page/404.html')

def pdf_report_create(request, request_number):
    template_path = 'other_temp/pdf_template.html'

    logo_path = os.path.join(settings.MEDIA_ROOT, 'NCTU-logo-1 (2).png')
    try:
        with open(logo_path, 'rb') as image_file:
            image_data = image_file.read()
        logo = base64.b64encode(image_data).decode('utf-8')
    except FileNotFoundError:
        logo = ''

    vacation = Vacation.objects.get(request_number=request_number)

    manager_signature_path = os.path.join(settings.MEDIA_ROOT, f'{vacation.manager_signature}') 
    try:
        with open(manager_signature_path, 'rb') as image_file:
            image_data = image_file.read()
        manager_signature = base64.b64encode(image_data).decode('utf-8')
    except FileNotFoundError:
        manager_signature = ''

    data = {
        "vacation": vacation,
        "department": vacation.employee.department.name,
        "logo": logo, 
        "manager_signature": manager_signature, 
    }

    context = {'data': data}

    html_string = render_to_string(template_path, context)

    try:
        client = pdfcrowd.HtmlToPdfClient('eslamt147', 'f9469b33bd059981cf203ba75288c057')
        
        client.convertStringToFile(html_string, 'Vacation_report.pdf')

        with open('Vacation_report.pdf', 'rb') as pdf_file:
            pdf = pdf_file.read()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        return response

    except pdfcrowd.Error as why:
        return HttpResponse("PDF conversion failed: {}".format(why)) 

    
from datetime import timedelta

def Rdepartment(request):
    departments = Department.objects.all()
    vacation_data = []

    start_date = None
    end_date = None
    department_id = None

    if request.method == 'POST':
        start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d')
        department_id = request.POST.get('department')

        vacation_records = Vacation.objects.filter(start_date__range=[start_date, end_date], end_date__range=[start_date, end_date], employee__department_id=department_id, status=2)
        total_users = User.objects.filter(department_id=department_id).count()
        current_date = start_date
        while current_date <= end_date:
            total_vacations = vacation_records.filter(start_date__lte=current_date, end_date__gte=current_date, status=2).count()
            total_vacations_users = vacation_records.filter(start_date__lte=current_date, end_date__gte=current_date, status=2)

            vacation_data.append({
                'date': current_date,
                'total_vacations': total_vacations,
                'total_users': total_users - total_vacations,
                'total_vacations_users' : total_vacations_users
            })

            current_date += timedelta(days=1)

    context = {
        'departments': departments,
        'vacation_data': vacation_data,
        'start_date': start_date,
        'end_date': end_date,
        'department_id': department_id,
    }
    return render(request, 'report/Rdepartment.html', context)


def Showuser(request):
    users = User.objects.all()
    query = request.GET.get('q')
    if query:
        users = users.filter(name__icontains=query)

    context = {
        'users': users
    }
    return render(request, 'report/Showuser.html', context)


from django.db.models import Sum

def Ruser(request, pk):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if start_date and end_date:
            start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            vacations = Vacation.objects.filter(employee__username=pk, start_date__range=[start_date, end_date], status=2)
            total_days = vacations.values('vacation_type').annotate(total_days=Sum('duration'))
        else:
            vacations = Vacation.objects.filter(employee__username=pk, status=2)
            total_days = vacations.values('vacation_type').annotate(total_days=Sum('duration'))
    else:
        vacations = Vacation.objects.filter(employee__username=pk, status=2)
        total_days = vacations.values('vacation_type').annotate(total_days=Sum('duration'))
    
    context = {
        'vacations': vacations,
        'total_days': total_days,
        'pk': pk,
    }
    return render(request, 'report/Ruser.html', context)