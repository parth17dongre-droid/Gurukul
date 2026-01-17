from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
import datetime

# Local imports
from .models import StudentProfile, AttendanceSession, Subject
from .forms import SignUpForm, TimetableUploadForm
from .utils import TimetableParser, update_attendance_stats

# --- 1. LANDING PAGE ---
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home/index.html')

# --- 2. SIGN UP VIEW ---
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile immediately
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
    return redirect('index')

# --- 5. DASHBOARD VIEW ---
@login_required(login_url='login')
def dashboard(request):
    # Ensure profile exists (failsafe)
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': profile,
    }
    return render(request, 'home/dashboard.html', context)

# --- 6. ATTENDANCE TRACKER ---
@login_required(login_url='login')
def attendance(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    today = datetime.date(2026,1,19)

    # Logic A: Handle "Reset"
    if request.method == 'POST' and 'reset_timetable' in request.POST:
        AttendanceSession.objects.filter(user=request.user).delete()
        Subject.objects.filter(user=request.user).delete()
        
        # Reset Stats
        profile.attendance_percentage = 0.0
        profile.save()
        return redirect('attendance')

    # Logic B: Handle Excel Upload
    if request.method == 'POST' and 'upload_file' in request.POST:
        form = TimetableUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            batch = form.cleaned_data['batch']
            
            # Call the Parser
            parser = TimetableParser()
            success, message = parser.parse_excel(excel_file, request.user, batch)
            
            if success:
                # Initialize stats to 0/0 immediately
                update_attendance_stats(request.user)
                return redirect('attendance')
            else:
                # If failed (e.g., wrong sheet), show error on page
                return render(request, 'home/attendance.html', {
                    'form': form,
                    'error': message,  # Show this in HTML
                    'has_timetable': False
                })

    # Logic C: Handle Marking Attendance
    if request.method == 'POST' and 'session_id' in request.POST:
        session_id = request.POST.get('session_id')
        status = request.POST.get('status')
        
        # Use get_object_or_404 for safety
        session = get_object_or_404(AttendanceSession, id=session_id, user=request.user)
        session.status = status
        session.save()
        
        # CRITICAL: Recalculate percentages immediately!
        update_attendance_stats(request.user)
        
        return redirect('attendance')

    # Logic D: Display Page
    has_timetable = Subject.objects.filter(user=request.user).exists()
    
    if not has_timetable:
        return render(request, 'home/attendance.html', {
            'form': TimetableUploadForm(),
            'has_timetable': False
        })

    # Fetch data for display
    todays_sessions = AttendanceSession.objects.filter(user=request.user, date=today).order_by('id')
    subjects = Subject.objects.filter(user=request.user)
    
    context = {
        'has_timetable': True,
        'todays_sessions': todays_sessions,
        'subjects': subjects,
        'today_date': today.strftime("%A, %d %B %Y"),
    }
    return render(request, 'home/attendance.html', context)
    