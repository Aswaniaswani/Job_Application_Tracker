from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import Profile, Job, Application,Notification

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')

        # Empty validation
        if not all([username, email, password1, password2, role]):
            messages.error(request, "All fields are required!")
            return redirect("register")

        # Password match
        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        # Duplicate email
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        # Duplicate username
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("register")

        # ❗ Prevent admin registration
        role = role.strip().lower()
        if role == "admin":
            messages.error(request, "Admin registration is not allowed")
            return redirect("register")

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        # Create profile safely
        Profile.objects.create(user=user, role=role)
        admins=User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(recipient=admin,message=f"New User registered :{username}({role.title()})")

        messages.success(request, "Registration successful. Please login.")
        return redirect("login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # profile create if missing
            profile, created = Profile.objects.get_or_create(user=user)

            if user.is_superuser:
                profile.role = "admin"
                profile.save()

                if not user.is_staff:
                    user.is_staff = True
                    user.save()


            # safe role check
            role = (profile.role or "").strip().lower()
            if role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'recruiter':
                return redirect('recruiter_dashboard')
            elif role == "candidate":
                if profile.profile_completed:
                    return redirect("candidate_dashboard")
                else:
                    return redirect("candidate_register")
        messages.error(request, "Invalid username or password")

    return render(request, "login.html")

def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        if User.objects.filter(username=username).exists():
            return redirect('set_new_password', username=username)
        else:
            messages.error(request, 'Username not found')

    return render(request, 'forgot_password.html')

def set_new_password(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, 'Invalid user')
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
        else:
            user.password = make_password(new_password)
            user.save()
            messages.success(request, 'Password updated successfully')
            return redirect('login')

    return render(request, 'set_new_password.html', {'username': username})



def logout_view(request):
    logout(request)
    return redirect('login')


# ---------------- RECRUITER ----------------

@login_required
def recruiter_dashboard(request):
    jobs = Job.objects.filter(recruiter=request.user)
    unread_count = request.user.notifications.filter(is_read=False).count()

    return render(request, "recruiter/recruiter_dashboard.html", {
        "jobs": jobs,
        "unread_count": unread_count
    })


@login_required
def create_job(request):
    if request.method == "POST":
        experience_required = request.POST.get("experience_required") == "on"
        min_experience = request.POST.get("min_experience") or None

        Job.objects.create(
            recruiter=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            location=request.POST['location'],
            status=request.POST.get('status', 'open'),
            experience_required=experience_required,
            min_experience=min_experience
        )
        #notify all candidates
        candidates=User.objects.filter(profile_role='candidate')
        for candidate in candidates:
            Notification.objects.create(recipient=candidate,message=f"New job posted :{job.title}")
        return redirect('recruiter_dashboard')

    return render(request, "recruiter/job_form.html")

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, recruiter=request.user)

    if request.method == "POST":
        job.title = request.POST['title']
        job.description = request.POST['description']
        job.location = request.POST['location']
        job.status = request.POST['status']

        job.experience_required = request.POST.get("experience_required") == "on"
        job.min_experience = request.POST.get("min_experience") or None

        job.save()
        return redirect('recruiter_dashboard')

    return render(request, "recruiter/job_form.html", {"job": job})

@login_required
def delete_job(request, job_id):
    job = Job.objects.get(id=job_id, recruiter=request.user)
    job.delete()
    return redirect('recruiter_dashboard')

@login_required
def recruiter_applications(request, job_id):
    job = Job.objects.get(id=job_id, recruiter=request.user)
    applications = Application.objects.filter(job=job)

    return render(request, "recruiter/applications.html", {
        "job": job,
        "applications": applications
    })

@login_required
def update_application_status(request, app_id):
    application = Application.objects.get(
        id=app_id,
        job__recruiter=request.user
    )

    if request.method == "POST":
        application.status = request.POST['status']
        application.save()

    return redirect('recruiter_applications', job_id=application.job.id)


# ---------------- CANDIDATE ----------------
@login_required
def candidate_dashboard(request):
    applications = Application.objects.filter(candidate=request.user)
    unread_count = request.user.notifications.filter(is_read=False).count()
    return render(request, "candidate/candidate_dashboard.html", {
        "applications": applications,
        "unread_count": unread_count,
    })


@login_required
def job_list(request):
    jobs = Job.objects.filter(status='open')
    return render(request, "candidate/job_list.html", {"jobs": jobs})


@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, status='open')
    profile = get_object_or_404(Profile, user=request.user)

    # ❌ Block freshers from experienced jobs
    if job.experience_required and not profile.is_experienced:
        messages.error(request, "This job is only for experienced candidates.")
        return redirect('job_list')

    # 🚫 Prevent duplicate application
    if Application.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('candidate_dashboard')

    if request.method == "POST":
        resume = request.FILES.get('resume')

        # ✅ Use uploaded resume OR existing profile resume
        final_resume = resume if resume else profile.resume

        if not final_resume:
            messages.error(request, "Please upload your resume.")
            return redirect(request.path)

        Application.objects.create(
            job=job,
            candidate=request.user,
            name=request.POST['name'],
            email=request.POST['email'],
            resume=final_resume
        )

        
        Notification.objects.create(recipient=job.recruiter,message=f"{request.user.username}applied for {job.title}")

        # 🔁 Update profile resume if new one uploaded
        if resume:
            profile.resume = resume
            profile.save()

        messages.success(request, "Job applied successfully!")
        return redirect('candidate_dashboard')

    return render(request, "candidate/apply_job.html", {
        "job": job,
        "profile": profile
    })

@login_required
def candidate_register(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        profile.phone = request.POST.get('phone')
        profile.is_experienced = request.POST.get('is_experienced') == 'on'
        profile.years_of_experience = request.POST.get('years_of_experience') or 0
        profile.resume = request.FILES.get('resume')

        profile.profile_completed = True
        profile.save()

        messages.success(request, "Profile completed successfully")
        return redirect('candidate_dashboard')

    return render(request, 'candidate_register.html', {'profile': profile})

# ---------------- ADMIN (READ ONLY) ----------------
@login_required
def admin_dashboard(request):
    profile = Profile.objects.filter(user=request.user).first()
    unread_count = request.user.notifications.filter(is_read=False).count()


    if not profile or profile.role != "admin":
        return redirect("login")
    context = {
        "total_users": User.objects.count(),
        "recruiters": Profile.objects.filter(role='recruiter').count(),
        "candidates": Profile.objects.filter(role='candidate').count(),
        "total_jobs": Job.objects.count(),
        "total_applications": Application.objects.count(),
        "unread_count": unread_count,
    }
    return render(request, "admin/admin_dashboard.html", context)

@login_required
def admin_jobs(request):
    return render(request, "admin/jobs.html", {
        "jobs": Job.objects.select_related('recruiter')
    })

@login_required
def admin_users(request):
    return render(request, "admin/users.html", {
        "profiles": Profile.objects.select_related('user')
    })

@login_required
def admin_applications(request):
    return render(request, "admin/applications.html", {
        "applications": Application.objects.select_related('job', 'candidate')
    })

@login_required
def notifications(request):
    user_notifications = request.user.notifications.order_by('-created_at')
    
    # Optional: mark all as read
    if request.method == "POST":
        user.notifications.filter(is_read=False).update(is_read=True)
        return redirect('notifications')

    return render(request, "notifications.html", {
        "notifications": user_notifications
    })