from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User,auth
from django.contrib import messages
import re
from .models import Employee, Employer, Section, Education, Experiance, Skills, Job, Type
from django.db.models import Q, Count
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import JsonResponse
import json
from django.db import transaction

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import redirect

# 1. Check if user is an Admin (superuser and staff)
def admin_check(user):
    return user.is_authenticated and user.is_superuser and user.is_staff

# 2. Check if user is a Staff (staff but not a superuser)
def staff_check(user):
    return user.is_authenticated and user.is_staff and not user.is_superuser

# 3. Check if user is a regular user (neither staff nor superuser)
def regular_user_check(user):
    return user.is_authenticated and not user.is_staff and not user.is_superuser

def check_username(request):
    """AJAX view to check if a username already exists."""
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)

def check_email(request):
    """AJAX view to check if an email is already in use."""
    email = request.GET.get('email', None)
    data = {
        'is_taken': User.objects.filter(email__iexact=email).exists()
    }
    return JsonResponse(data)

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        fullname = request.POST['fullname']
        user_type = request.POST['user_type']
        email = request.POST.get('email')

        # Check if the username is already in use
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'Username is already in use.')
        # Check if the email is already in use
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email is already in use.')
        else:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Invalid email format.')

            # Password Validation
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            elif not re.search(r'[A-Z]', password):
                messages.error(request, 'Password must contain at least one uppercase letter.')
            elif not re.search(r'[a-z]', password):
                messages.error(request, 'Password must contain at least one lowercase letter.')
            elif not re.search(r'\d', password):
                messages.error(request, 'Password must contain at least one digit.')
            elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                messages.error(request, 'Password must contain at least one special character.')
            elif password != confirm_password:
                messages.error(request, 'Passwords do not match.')
            else:
                # Create the user if there are no validation errors
                is_staff = True if user_type == 'employer' else False
                user = User.objects.create_user(username=username, password=password, is_staff=is_staff, email=email)
                user.save()

                # Create corresponding Employee or Employer record
                if user_type == 'employer':
                    Employer.objects.create(user=user, name=fullname)
                else:
                    Employee.objects.create(user=user, fullname=fullname)

                
                messages.success(request, 'Account created successfully.')
                return redirect('login')  # Redirect to login page

    return render(request, 'signup.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            # Redirect based on user type
            if user.is_superuser:
                return redirect('admin_dashboard')  # Superuser page
            elif user.is_staff:
                return redirect('employer_dashboard')  # Employer page
            else:
                return redirect('jobseeker_dashboard')  # Job Seeker page
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('login')  # Redirect to login page if not a superuser

    # Count jobs where employee is null and approval is false
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()

    context = {
        'notification_count': notification_count,
    }
    
    return render(request, 'admin_dashboard.html', context)

def home(request):
    return render(request, 'home.html')

def base(request):
    return render(request, 'base.html')

def hoshome(request):
    return render(request, 'hoshome.html')

@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def manage_sections(request):
    sections = Section.objects.all()
    # return redirect('manage_sections')
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()

    context = {
        'notification_count': notification_count, 'sections': sections
    }
    
    return render(request, 'manage_sections.html', context)

@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def add_section(request):
    if request.method == 'POST':
        section_name = request.POST.get('section_name')
        if section_name:
            Section.objects.create(name=section_name)
            return redirect('manage_sections')

    sections = Section.objects.all()
    return render(request, 'manage_sections.html', {'sections': sections})

@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def manage_types(request):
    types = Type.objects.all()
    # return redirect('manage_sections')
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()

    context = {
        'notification_count': notification_count, 'types': types
    }
    
    return render(request, 'manage_types.html', context)

@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def add_type(request):
    if request.method == 'POST':
        type_name = request.POST.get('type_name')
        if type_name:
            Type.objects.create(name=type_name)
            return redirect('manage_types')

    types = Type.objects.all()
    return render(request, 'manage_types.html', {'types': types})


def lgout(request):
    auth.logout(request)
    return redirect ('login')

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def employer_dashboard(request):
    # Get the logged-in user's employer profile
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    # Determine if the complete registration button should be shown
    show_complete_registration_button = not employer.status

    return render(request, 'employer_dashboard.html', {
        'show_complete_registration_button': show_complete_registration_button,'employer':employer, 'count':count
    })

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def jobseeker_dashboard(request):
    employee = Employee.objects.get(user=request.user)
    if employee.section is None:
        show_complete_registration_button = True
    else:
        show_complete_registration_button = False
    
    employee = Employee.objects.get(user=request.user)
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()
    
    #job_count = Job.objects.filter(section=employee.section, employee__isnull=True).count()

    return render(request, 'jobseeker_dashboard.html', {
        'show_complete_registration_button': show_complete_registration_button,
        'job_count': job_count,
        'employee':employee
    })


@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def complete_registration(request):
    employee = Employee.objects.get(user=request.user)
    sections = Section.objects.all()

    if request.method == 'POST':
        employee.image = request.FILES.get('image')
        employee.date = request.POST['date']
        employee.address = request.POST['address']
        employee.phonenumber = request.POST['phonenumber']
        employee.pincode = request.POST['pincode']
        employee.state = request.POST['state']
        employee.city = request.POST['city']
        employee.resume = request.FILES.get('resume')
        employee.section_id = request.POST['section']
        employee.save()
        return redirect('add_education')
    
    employee = Employee.objects.get(user=request.user)
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()
        

    return render(request, 'complete_registration.html', {
        'employee': employee,
        'sections': sections,
        'job_count':job_count
    })

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def add_education(request):
    employee = Employee.objects.get(user=request.user)

    if request.method == 'POST':
        if 'add' in request.POST:
            # Handle adding a new education entry
            course = request.POST['course']
            institute = request.POST['institute']
            fromd = request.POST['fromd']
            tod = request.POST['tod']
            document = request.FILES.get('document')

            Education.objects.create(
                course=course,
                institute=institute,
                fromd=fromd,
                tod=tod,
                document=document,
                employee=employee
            )
        elif 'submit' in request.POST:
            # Redirect to the dashboard after final submission
            return redirect('add_experience')

    # Get all education entries for the logged-in employee
    education_list = Education.objects.filter(employee=employee)

    employee = Employee.objects.get(user=request.user)
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()

    return render(request, 'add_education.html', {
        'education_list': education_list,'job_count':job_count
    })

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def add_experience(request):
    employee = Employee.objects.get(user=request.user)

    if request.method == 'POST':
        if 'add' in request.POST:
            # Handle adding a new experience entry
            position = request.POST['position']
            institute = request.POST['institute']
            description = request.POST['description']
            fromd = request.POST['fromd']
            tod = request.POST['tod']
            document = request.FILES.get('document')

            Experiance.objects.create(
                position=position,
                institute=institute,
                description=description,
                fromd=fromd,
                tod=tod,
                document=document,
                employee=employee
            )
        elif 'submit' in request.POST:
            # Redirect to the dashboard after final submission
            return redirect('add_skills')

    # Get all experience entries for the logged-in employee
    experience_list = Experiance.objects.filter(employee=employee)

    employee = Employee.objects.get(user=request.user)
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()

    return render(request, 'add_experience.html', {
        'experience_list': experience_list,
        'job_count':job_count
    })

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def add_skills(request):
    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()




    employee = Employee.objects.get(user=request.user)

    if request.method == 'POST':
        if 'add' in request.POST:
            # Handle adding a new skill entry
            name = request.POST['name']

            Skills.objects.create(
                name=name,
                employee=employee
            )
        elif 'submit' in request.POST:
            # Redirect to the dashboard after final submission
            # messages.success(request, 'Registration completed successfully.')
            # return redirect('jobseeker_dashboard')
            error_message = "Profile details Updated Successfully"
            return render(request, 'jobseeker_dashboard.html', {'error_message': error_message,'job_count':job_count,'employee':employee})

    # Get all skill entries for the logged-in employee
    skills_list = Skills.objects.filter(employee=employee)

    return render(request, 'add_skills.html', {
        'skills_list': skills_list,
        'job_count':job_count
    })

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def profile(request):
    # Get the logged-in user's employee profile
    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()

    # Get all related experience, education, and skills entries
    experience_list = Experiance.objects.filter(employee=employee)
    education_list = Education.objects.filter(employee=employee)
    skills_list = Skills.objects.filter(employee=employee)

    # Render the profile page with all the data
    return render(request, 'profile.html', {
        'employee': employee,
        'experience_list': experience_list,
        'education_list': education_list,
        'skills_list': skills_list,
        'job_count':job_count
    })

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def complete_employer_registration(request):
    employer = Employer.objects.get(user=request.user)

    if request.method == 'POST':
        # Update the employer's details
        employer.logo = request.FILES.get('logo')
        employer.address = request.POST.get('address')
        employer.phonenumber = request.POST.get('phonenumber')
        employer.pincode = request.POST.get('pincode')
        employer.state = request.POST.get('state')
        employer.city = request.POST.get('city')
        
        # New fields
        employer.description = request.POST.get('description')
        # employer.section = request.POST.get('section')
        employer.document = request.FILES.get('document')

        # Change status to True after completion
        employer = Employer.objects.get(user=request.user)
        jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
        count = jobs.count()
        employer.status = True  
        employer.save()
        error_message = "Profile details Updated Successfully"
        return render(request, 'employer_dashboard.html', {'error_message': error_message, 'employer':employer,'count':count})
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()

    return render(request, 'complete_employer_registration.html', {
        'employer': employer,'count':count
    })


@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def add_job(request):
    try:
        employer = Employer.objects.get(user=request.user)
    except Employer.DoesNotExist:
        # Handle the case where Employer does not exist
        return redirect('dashboard')  # Redirect or show an error message

    # Check if employer's city is Null
    if not employer.city:
        return redirect('complete_employer_registration')  # Redirect to complete registration

    if request.method == 'POST':
        section_id = request.POST.get('section')
        title = request.POST.get('title')
        experiance = request.POST.get('experiance')
        skills = request.POST.get('skills')
        city = request.POST.get('city')
        fromd = request.POST.get('fromd')
        tod = request.POST.get('tod')
        type_id = request.POST.get('type')
        education = request.POST.get('education')
        description = request.POST.get('description')

        # Basic validation
        if section_id and title and city and type_id and education and description:
            try:
                section = Section.objects.get(id=section_id)
                type = Type.objects.get(id=type_id)
                # Create a new Job instance
                job = Job(
                    section=section,
                    title=title,
                    employer=employer,
                    experiance=experiance,
                    skills=skills,
                    city=city,
                    fromd=fromd,
                    tod=tod,
                    type=type,
                    education=education,
                    description=description
                )
                job.save()
                employer = Employer.objects.get(user=request.user)
                jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
                count = jobs.count()
                error_message = "Job added successfully! Wait for the confirmation from admin "
                return render(request, 'employer_dashboard.html', {'error_message': error_message,'employer':employer,'count':count})
            except Section.DoesNotExist:
                messages.error(request, "Selected section does not exist.")
        else:
            messages.error(request, "All fields are required.")

    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    sections = Section.objects.all()
    types = Type.objects.all()
    return render(request, 'add_job.html', {
        'sections': sections,
        'types': types,'count':count,
        'submitted_data': request.POST or {}
    })


    
@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def pending_jobs(request):
    jobs = Job.objects.filter(approval__isnull=True,employee__isnull=True)
    
    # return redirect('manage_sections')
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()

    context = {
        'notification_count': notification_count, 'jobs': jobs
    }
    
    return render(request, 'pending_jobs.html', context)


@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def xapprove_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.approval = True
    job.save()
    jobs = Job.objects.filter(approval__isnull=True,employee__isnull=True)
    
    # return redirect('manage_sections')
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()

    context = {
        'notification_count': notification_count, 'jobs': jobs
    }
    
    return render(request, 'pending_jobs.html', context)


@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def xreject_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.approval = False
    job.save()
    jobs = Job.objects.filter(approval__isnull=True,employee__isnull=True)
    
    # return redirect('manage_sections')
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()

    context = {
        'notification_count': notification_count, 'jobs': jobs
    }
    
    return render(request, 'pending_jobs.html', context)


@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def matching_jobs(request):
    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()






    employee = Employee.objects.get(user=request.user)
    
    # Step 1: Identify job titles, sections, and employers where there are conflicting entries
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )
    filtered_jobs = filtered_jobs.order_by('-id')

    return render(request, 'matching_jobs.html', {'jobs': filtered_jobs,'job_count':job_count})


@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def apply_job(request, job_id):
    
    original_job = get_object_or_404(Job, id=job_id)
    employee = Employee.objects.get(user=request.user)
    
    if not employee.section:
        return redirect('complete_registration')  # Redirect to complete registration
    
    # Create a new job entry with the same details as the original job, but with the logged-in employee
    new_job = Job.objects.create(
        title=original_job.title,
        section=original_job.section,
        employer=original_job.employer,
        employee=employee,
        approval=False,
        experiance=original_job.experiance,
        skills=original_job.skills,
        city=original_job.city,
    )

    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()
    
    # Redirect to the matching jobs page
    error_message = "Job applied successfully! Wait for the decision from the Employer "
    return render(request, 'jobseeker_dashboard.html', {'error_message': error_message,'employee':employee,'job_count':job_count})
    

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def view_job_details(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'view_job_details.html', {'job': job})


@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def employer_job_applicants(request):
    # Get the logged-in employer
    jobs_with_applicants = Job.objects.filter(
        employer__user=request.user,
        employee__isnull=False, status=Job.NONE, is_saved=False
    ).order_by('title', 'section', 'employer')  # Order by title, section, and employer

    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()

    return render(request, 'employer_job_applicants.html', {'jobs_with_applicants': jobs_with_applicants,'count':count})

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def view_employee_details(request, employee_id):
    # Get the employee object based on the provided ID
    employee = get_object_or_404(Employee, id=employee_id)
    
    # Get related education, experience, and skills
    education_details = Education.objects.filter(employee=employee)
    experience_details = Experiance.objects.filter(employee=employee)
    skills_details = Skills.objects.filter(employee=employee)

    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()

    return render(request, 'view_employee_details.html', {
        'employee': employee,
        'education_details': education_details,
        'experience_details': experience_details,
        'skills_details': skills_details,
        'count':count
    })

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def filtered_jobs(request):
    employee = Employee.objects.get(user=request.user)
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()
    
    
    employee = Employee.objects.get(user=request.user)
    
    
    # Get the filter values from the request
    title_keyword = request.GET.get('title_keyword', '')
    section_id = request.GET.get('section', '')
    type_id = request.GET.get('type', '')
    city_keyword = request.GET.get('city_keyword', '')

    # Step 1: Identify job titles, sections, and employers where there are conflicting entries
    conflicting_jobs = Job.objects.filter( 
        # section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        # section=employee.section,
        employee__isnull=True, approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    # Apply additional filters
    if title_keyword:
        filtered_jobs = filtered_jobs.filter(title__icontains=title_keyword)
    
    if section_id:
        filtered_jobs = filtered_jobs.filter(section_id=section_id)

    if type_id:
        filtered_jobs = filtered_jobs.filter(type_id=type_id)
    
    if city_keyword:
        filtered_jobs = filtered_jobs.filter(employer__city__icontains=city_keyword)

    filtered_jobs = filtered_jobs.order_by('-id')

    # Fetch all sections for the dropdown
    sections = Section.objects.all()
    types = Type.objects.all()

    return render(request, 'filtered_jobs.html', {
        'jobs': filtered_jobs,
        'sections': sections,
        'types': types,
        'title_keyword': title_keyword,
        'section_id': section_id,
        'city_keyword': city_keyword,
        'job_count': job_count
    })


def ufiltered_jobs(request):
    filtered_jobs = Job.objects.filter(
        employee__isnull=True, approval=True
    )
    
    # Get the filter values from the request
    title_keyword = request.GET.get('title_keyword', '')
    section_id = request.GET.get('section', '')
    type_id = request.GET.get('type', '')
    city_keyword = request.GET.get('city_keyword', '')

    

    # Step 1: Identify job titles, sections, and employers where there are conflicting entries
    # conflicting_jobs = Job.objects.filter(
    #     # section=employee.section
    # ).filter(
    #     Q(employee__isnull=True) | Q(employee=employee)
    # ).values('title', 'section', 'employer').distinct()

    # # Step 2: Filter out the jobs that have conflicting entries
    # filtered_jobs = Job.objects.filter(
    #     # section=employee.section,
    #     employee__isnull=True
    # )

    # for job in conflicting_jobs:
    #     if Job.objects.filter(
    #         title=job['title'],
    #         section=job['section'],
    #         employer=job['employer'],
    #         employee=employee
    #     ).exists():
    #         filtered_jobs = filtered_jobs.exclude(
    #             title=job['title'],
    #             section=job['section'],
    #             employer=job['employer']
    #         )

    # Apply additional filters
    if title_keyword:
        filtered_jobs = filtered_jobs.filter(title__icontains=title_keyword)
    
    if section_id:
        filtered_jobs = filtered_jobs.filter(section_id=section_id)

    if type_id:
        filtered_jobs = filtered_jobs.filter(type_id=type_id)
    
    if city_keyword:
        filtered_jobs = filtered_jobs.filter(employer__city__icontains=city_keyword)

    filtered_jobs = filtered_jobs.order_by('-id')

    # Fetch all sections for the dropdown
    sections = Section.objects.all()
    types = Type.objects.all()

    return render(request, 'ufiltered_jobs.html', {
        'jobs': filtered_jobs,
        'sections': sections,
        'types': types,
        'title_keyword': title_keyword,
        'section_id': section_id,
        'type_id': type_id,
        'city_keyword': city_keyword
    })

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def employee_jobs(request):
    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()



    # Get the signed-in employee
    employee = Employee.objects.get(user=request.user)
    # Retrieve all job entries where the employee foreign key matches the signed-in employee
    jobs = Job.objects.filter(employee=employee,is_saved=False)
    
    context = {
        'jobs': jobs,'job_count':job_count
    }
    return render(request, 'employee_jobs.html', context)

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def job_detail(request, job_id):
    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'job_detail.html', {'job': job,'job_count':job_count})

@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def job_details(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'job_details.html', {'job': job})

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def employer_job_list(request):
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval=True)
    return render(request, 'employer_job_list.html', {'jobs': jobs,'count':count})

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def employer_edit_job(request, job_id):
    employer = Employer.objects.get(user=request.user)
    job = get_object_or_404(Job, id=job_id, employer=employer)

    if request.method == 'POST':
        title = request.POST.get('title')
        section_id = request.POST.get('section')
        experiance = request.POST.get('experiance')
        skills = request.POST.get('skills')
        city = request.POST.get('city')
        fromd = request.POST.get('fromd')
        tod = request.POST.get('tod')
        type_id = request.POST.get('type')
        education = request.POST.get('education')
        description = request.POST.get('description')

        # Validate required fields
        if title and section_id and experiance and skills and city and type_id and education and description:
            job.title = title
            job.section_id = section_id
            job.experiance = experiance
            job.skills = skills
            job.city = city
            job.fromd = fromd if fromd else None  # Convert to Date if not empty
            job.tod = tod if tod else None        # Convert to Date if not empty
            job.type_id = type_id
            job.education = education
            job.description = description
            
            job.save()
            error_message = "The Job is updated "
            employer = Employer.objects.get(user=request.user)
            jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
            count = jobs.count()
            jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval=True)
            messages.success(request, "The Job is updated")
            return redirect('employer_job_list')
            
        else:
            messages.error(request, "All fields are required.")

    sections = Section.objects.all()
    types = Type.objects.all()
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    return render(request, 'employer_edit_job.html', {
        'job': job,
        'sections': sections,
        'types': types,
        'count':count
    })

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def employer_delete_job(request, job_id):
    employer = Employer.objects.get(user=request.user)
    job = get_object_or_404(Job, id=job_id, employer=employer)

    if request.method == 'POST':
        error_message = "The Job is deleted "
        jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
        count = jobs.count()
        jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval=True)
        job.delete()
        messages.success(request, "The job is delted")
        return redirect('employer_job_list')
        return render(request, 'employer_job_list.html', {'error_message': error_message,'count':count,'jobs':jobs})
    
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()

    return render(request, 'employer_confirm_delete_job.html', {'job': job,'count':count})

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def xemployer_job_list(request):
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    return render(request, 'xemployer_job_list.html', {'jobs': jobs,'count':count})


@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def acknowledge_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.noti = True
    job.save()
    return redirect('xemployer_job_list')  # Replace 'job_list' with the name of the URL for this page

@login_required(login_url='login')
def candidate_details(request):
    return render(request, 'candidate_details.html')

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def approve_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, employer__user=request.user)
    job.status = Job.APPROVED
    job.save()
    
    
    # Send email notification to the candidate
    send_mail(
        'Job Application Status',
        f'Dear {job.employee.fullname}, your application for the position of {job.title} has been approved by {job.employer.name}.',
        'from@example.com',
        [job.employee.user.email],
        fail_silently=False,
    )
    jobs_with_applicants = Job.objects.filter(
        employer__user=request.user,
        employee__isnull=False, status=Job.NONE
    ).order_by('title', 'section', 'employer')  # Order by title, section, and employer
    error_message = "The candidate is approved "
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    return render(request, 'employer_job_applicants.html', {'error_message': error_message,'jobs_with_applicants': jobs_with_applicants,'count':count})

    
 

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def reject_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, employer__user=request.user)
    job.status = Job.REJECTED
    job.save()
    
    # Send email notification to the candidate
    send_mail(
        'Job Application Status',
        f'Dear {job.employee.fullname}, we regret to inform you that your application for the position of {job.title} has been rejected by {job.employer.name}.',
        'from@example.com',
        [job.employee.user.email],
        fail_silently=False,
    )
    jobs_with_applicants = Job.objects.filter(
        employer__user=request.user,
        employee__isnull=False, status=Job.NONE
    ).order_by('title', 'section', 'employer')  # Order by title, section, and employer
    error_message = "The candidate is rejected "
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    return render(request, 'employer_job_applicants.html', {'error_message': error_message,'jobs_with_applicants': jobs_with_applicants,'count':count})

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def mark_as_pending(request, job_id):
    job = get_object_or_404(Job, id=job_id, employer__user=request.user)
    job.status = Job.PENDING
    job.save()
    
    # Send email notification to the candidate
    send_mail(
        'Job Application Status',
        f'Dear {job.employee.fullname}, your application for the position of {job.title} is still under consideration by {job.employer.name}.',
        'from@example.com',
        [job.employee.user.email],
        fail_silently=False,
    )
    
    jobs_with_applicants = Job.objects.filter(
        employer__user=request.user,
        employee__isnull=False, status=Job.NONE
    ).order_by('title', 'section', 'employer')  # Order by title, section, and employer
    error_message = "The candidate is added to the pending list "
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    return render(request, 'employer_job_applicants.html', {'error_message': error_message,'jobs_with_applicants': jobs_with_applicants,'count':count})

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def view_profile(request):
    # Assuming the logged-in user is linked to an Employer
    employer = get_object_or_404(Employer, user=request.user)
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    return render(request, 'view_profile.html', {'employer': employer,'count':count})

@login_required(login_url='login')
def edit_profile(request):
    employer = get_object_or_404(Employer, user=request.user)

    if request.method == 'POST':
        employer.name = request.POST.get('name')
        if request.FILES.get('logo'):
            employer.logo = request.FILES['logo']
        employer.address = request.POST.get('address')
        employer.phonenumber = request.POST.get('phonenumber')
        employer.pincode = request.POST.get('pincode')
        employer.state = request.POST.get('state')
        employer.city = request.POST.get('city')
        employer.description = request.POST.get('description')
        # employer.section = request.POST.get('section')
        if request.FILES.get('document'):
            employer.document = request.FILES['document']

        employer.save()
        return redirect('view_profile')

    return render(request, 'edit_profile.html', {'employer': employer})

@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def employer_job_status(request):
    # Get the logged-in employer
    jobs_with_applicants = Job.objects.filter(
        employer__user=request.user,
        employee__isnull=False
    ).filter(
        Q(status=Job.APPROVED) | Q(status=Job.PENDING)
    ).order_by('title', 'section', 'employer')  # Order by title, section, and employer
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()

    return render(request, 'employer_job_status.html', {'jobs_with_applicants': jobs_with_applicants,'count':count})

@login_required(login_url='login')
def base(request):
    # Check if the user is a superuser
    if not request.user.is_superuser:
        return redirect('login')  # Redirect to login page if not a superuser

    # Count jobs where employee is null and approval is false
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()

    context = {
        'notification_count': notification_count,
    }
    
    return render(request, 'base.html', context)

@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def delete_section(request, section_id):
    # Get the section to be deleted
    section = get_object_or_404(Section, id=section_id)
    
    # Retrieve all employees associated with the section
    employees = Employee.objects.filter(section=section)
    
    # Delete all job listings associated with the section
    Job.objects.filter(section=section).delete()
    
    # Delete associated employees
    # Get user ids of employees to delete
    user_ids = employees.values_list('user_id', flat=True)
    employees.delete()
    
    # Delete associated users
    User.objects.filter(id__in=user_ids).delete()
    
    # Delete the section itself
    section.delete()
    
    # Retrieve the updated list of sections and notification count
    sections = Section.objects.all()
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()
    error_message = "The selected job section deleted succesfully "
    # Prepare context for rendering the template
    context = {
        'notification_count': notification_count,
        'error_message': error_message
    }
    
    messages.success(request, "The selected job section was deleted successfully.")
    
    # Redirect to the admin dashboard
    return redirect('admin_dashboard')


@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def delete_type(request, type_id):
    # Get the type to be deleted
    type_obj = get_object_or_404(Type, id=type_id)
    
    # Delete all job listings associated with the type
    Job.objects.filter(type=type_obj).delete()
    
    # Delete the type itself
    type_obj.delete()
    
    # Retrieve the updated list of types and notification count
    types = Type.objects.all()
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()
    error_message = "The selected job type deleted succesfully "
    # Prepare context for rendering the template
    context = {
        'notification_count': notification_count,
        'error_message': error_message
    }
    
    messages.success(request, "The selected job type was deleted successfully.")
    
    # Redirect to the admin dashboard
    return redirect('admin_dashboard')

@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def list_employers(request):
    employers = Employer.objects.all()
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()

    context = {
        'notification_count': notification_count, 'employers': employers
    }
    
    return render(request, 'list_employers.html', context)

@login_required(login_url='login')
@user_passes_test(admin_check, login_url='login') 
def delete_employer(request, employer_id):
    employer = get_object_or_404(Employer, id=employer_id)
    employers = Employer.objects.all()
    notification_count = Job.objects.filter(employee__isnull=True, approval__isnull=True).count()
    
    # Store the user before deleting the employer
    user = employer.user
    
    # Delete the employer
    employer.delete()
    
    # Delete the associated user
    if user:
        user.delete()
    
    context = {
        'notification_count': notification_count, 'employers': employers
    }
    
    return render(request, 'list_employers.html', context)

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def save_job(request, job_id):
    
    original_job = get_object_or_404(Job, id=job_id)
    employee = Employee.objects.get(user=request.user)
    
    if not employee.section:
        return redirect('complete_registration')  # Redirect to complete registration
    
    # Create a new job entry with the same details as the original job, but with the logged-in employee
    new_job = Job.objects.create(
        title=original_job.title,
        section=original_job.section,
        employer=original_job.employer,
        employee=employee,
        approval=False,
        experiance=original_job.experiance,
        skills=original_job.skills,
        is_saved=True,
    )

    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()
    
    # Redirect to the matching jobs page
    error_message = "Job added to the saved list "
    return render(request, 'jobseeker_dashboard.html', {'error_message': error_message,'employee':employee,'job_count':job_count})


@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def saved_jobs(request):
    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()






    employee = Employee.objects.get(user=request.user)
    
    filtered_jobs = Job.objects.filter(employee=employee,is_saved=True)
    filtered_jobs = filtered_jobs.order_by('-id')

    return render(request, 'saved_jobs.html', {'jobs': filtered_jobs,'job_count':job_count})

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def save_details(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'save_details.html', {'job': job})

@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def apply_save(request, job_id):

    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()

######################################## code starts here above render for notification #############################


    # Retrieve the job using the provided job_id
    job_to_save = get_object_or_404(Job, id=job_id)
    
    # Check if there are any other jobs with the same attributes (excluding the current one)
    has_matching_job = Job.objects.filter(
        section=job_to_save.section,
        title=job_to_save.title,
        employer=job_to_save.employer,
        experiance=job_to_save.experiance,
        skills=job_to_save.skills,
        approval=True
    ).exclude(id=job_id).exists()

    if has_matching_job:
        # Update the is_saved field to False for the current job
        job_to_save.is_saved = False
        job_to_save.save()

        # Provide success feedback to the user
        error_message = "Job applied successfully! Wait for the decision from the Employer."
        return render(request, 'jobseeker_dashboard.html', {'error_message': error_message,'employee':employee,'job_count':job_count})
    else:
        # If no matching job is found, display an appropriate message
        error_message = 'The company is no longer inviting applicants.'
        return render(request, 'jobseeker_dashboard.html', {'error_message': error_message,'employee':employee,'job_count':job_count})


@login_required(login_url='login')
@user_passes_test(regular_user_check, login_url='login')
def undo_save(request, job_id):

    # Get the job entry to delete
    job_to_delete = get_object_or_404(Job, id=job_id)

    # Delete the job entry
    job_to_delete.delete()

    

    ##########################################   main above  ####################################
    
    employee = Employee.objects.get(user=request.user)
    
    
    # Count the number of jobs matching the employee's section where employee is null
    conflicting_jobs = Job.objects.filter(
        section=employee.section
    ).filter(
        Q(employee__isnull=True) | Q(employee=employee)
    ).values('title', 'section', 'employer').distinct()

    # Step 2: Filter out the jobs that have conflicting entries
    filtered_jobs = Job.objects.filter(
        section=employee.section,
        employee__isnull=True,approval=True
    )

    for job in conflicting_jobs:
        if Job.objects.filter(
            title=job['title'],
            section=job['section'],
            employer=job['employer'],
            employee=employee
        ).exists():
            filtered_jobs = filtered_jobs.exclude(
                title=job['title'],
                section=job['section'],
                employer=job['employer']
            )

    job_count = filtered_jobs.count()

    # Add a success message
    error_message = "The job entry has been successfully removed from the saved list."

    # Redirect back to the jobseeker dashboard (or wherever you prefer)
    return render(request, 'jobseeker_dashboard.html', {'error_message': error_message,'employee':employee,'job_count':job_count})


@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login')
def employer_all_list(request):
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    jobs = Job.objects.filter(employer=employer, employee__isnull=True)
    return render(request, 'employer_all_list.html', {'jobs': jobs,'count':count})


@login_required(login_url='login')
@user_passes_test(staff_check, login_url='login') 
def job_det(request, job_id):
    employer = Employer.objects.get(user=request.user)
    jobs = Job.objects.filter(employer=employer, employee__isnull=True, approval__isnull=False, noti=False)
    count = jobs.count()
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'job_det.html', {'job': job,'count':count})