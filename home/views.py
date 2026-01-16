from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
import datetime

# Local imports for your App logic
from .models import StudentProfile, AttendanceSession, Subject
from .forms import SignUpForm, TimetableUploadForm
from .utils import TimetableParser, update_attendance_stats

# --- 1. LANDING PAGE ---
def index(request):
    return render(request, 'home/index.html')

# --- 2. SIGN UP VIEW ---
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a profile for the new user immediately
            StudentProfile.objects.create(user=user)
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    
    return render(request, 'home/signup.html', {'form': form})

# --- 3. LOGIN VIEW ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'home/login.html', {'form': form})

# --- 4. LOGOUT VIEW ---
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('index')

# --- 5. DASHBOARD VIEW ---
@login_required(login_url='login')
def dashboard(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    context = {'profile': profile}
    return render(request, 'home/dashboard.html', context)

# --- 6. ATTENDANCE TRACKER (Unified View) ---
# home/views.py

@login_required(login_url='login')
def attendance(request):
    # Logic A: Handle "Reset / Re-upload"
    if request.method == 'POST' and 'reset_timetable' in request.POST:
        # Delete everything for this user
        AttendanceSession.objects.filter(user=request.user).delete()
        Subject.objects.filter(user=request.user).delete()
        
        # Reset profile stats
        profile = request.user.studentprofile
        profile.attendance_percentage = 0.0
        profile.save()
        
        return redirect('attendance')

    # Logic B: Handle Excel Upload (Existing code)
    if request.method == 'POST' and 'upload_file' in request.POST:
        form = TimetableUploadForm(request.POST, request.FILES)
        if form.is_valid():
            parser = TimetableParser()
            parser.parse_excel(
                request.FILES['file'], 
                request.user, 
                form.cleaned_data['batch']
            )
            return redirect('attendance')

    # Logic C: Handle Marking Attendance (Existing code)
    if request.method == 'POST' and 'session_id' in request.POST:
        try:
            session = AttendanceSession.objects.get(id=request.POST.get('session_id'))
            if session.user == request.user:
                session.status = request.POST.get('status')
                session.save()
                update_attendance_stats(request.user)
            return redirect('attendance')
        except AttendanceSession.DoesNotExist:
            pass

    # Logic D: Display Page
    today = datetime.date.today()
    context = {
        'form': TimetableUploadForm(),
        'has_timetable': AttendanceSession.objects.filter(user=request.user).exists(),
        'today_date': today.strftime("%A, %d %B"),
        'todays_sessions': AttendanceSession.objects.filter(user=request.user, date=today),
        'subjects': Subject.objects.filter(user=request.user),
    }
    return render(request, 'home/attendance.html', context)