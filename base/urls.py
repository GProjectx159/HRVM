from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.home, name="home"),
    path("Home/", views.home_after, name="home_after"),

    path("signup/", views.signup, name="signup"),
    path('login/', views.loginUser, name='login'),
    path('logout/', views.logoutUser, name='logout'),

    path('profile/<str:username>/', views.userprofile, name='user-profile'),
    path('usersRequests/', views.usersRequests, name='usersRequests'),
    path('AcceptUsers/<str:username>/', views.acceptUsers, name='AcceptUsers'),
    path('deleteUser/<str:username>/', views.deleteUser, name='deleteUser'),
    path('updateUser/<str:username>/', views.updateUser, name='updateUser'),

    path('manageDepartment/', views.manageDepartment, name='manageDepartment'),
    path('editdepartment/<int:department_id>/', views.editdepartment, name='editdepartment'),


    path('reset/password/', views.CustomPasswordResetView.as_view(), name='reset_password'),
    path('reset/password/sent/', auth_views.PasswordResetDoneView.as_view(template_name='registration/reset_password_sent.html'), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/reset.html'), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/reset_password_complete.html'), name='password_reset_complete'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html', success_url = reverse_lazy("home") ),  name='password_change'),

    path('requestView/', views.requestView, name='requestView'),
    path('vacationRequest/', views.vacationRequest, name='vacationRequest'),
    # path('saveRequest/', views.saveRequest, name='saveRequest'),
    path('AcceptRequest/', views.AcceptRequest, name='AcceptRequest'),
    path('showRequest/<str:pk>/', views.showRequest, name='showRequest'),
    path('showMyRequest/<str:pk>/', views.showMyRequest, name='showMyRequest'),

    path('approve/<int:request_number>/', views.approve_vacation, name='approve_vacation'),
    path('reject/<int:request_number>/', views.reject_vacation, name='reject_vacation'),

    path('pdf_view/<int:request_number>/', views.pdf_report_create, name="pdf_view"),
    path('pdf_view/<str:department>/', views.pdf_report_department, name="pdf_view_department"),


    path('Rdepartment/', views.Rdepartment, name="Rdepartment"),
    path('Showuser/', views.Showuser, name="Showuser"),
    path('Ruser/<str:pk>/', views.Ruser, name="Ruser"),
    path('Rday/', views.Rday, name="Rday"),


]



