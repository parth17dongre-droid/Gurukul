from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import datetime

# Local imports
from .models import StudentProfile, AttendanceSession, Subject, AINote
from .forms import SignUpForm, TimetableUploadForm
from .utils import TimetableParser, update_attendance_stats
from .ai_utils import generate_notes, generate_deep_dive


# ==========================================
# 🔐 AUTHENTICATION & LANDING
# ==========================================

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home/index.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            StudentProfile.objects.create(user=user)
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    
    return render(request, 'home/signup.html', {'form': form})

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

def logout_view(request):
    logout(request)
    return redirect('index')

# ==========================================
# 📊 DASHBOARD & ATTENDANCE
# ==========================================

@login_required(login_url='login')
def dashboard(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    context = {'profile': profile}
    return render(request, 'home/dashboard.html', context)

@login_required(login_url='login')
def attendance(request):
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    # ⚠️ DEV MODE: HARDCODED DATE (Change to datetime.date.today() later)
    today = datetime.date(2026, 1, 19) 

    # Logic A: Reset
    if request.method == 'POST' and 'reset_timetable' in request.POST:
        AttendanceSession.objects.filter(user=request.user).delete()
        Subject.objects.filter(user=request.user).delete()
        profile.attendance_percentage = 0.0
        profile.save()
        return redirect('attendance')

    # Logic B: Upload
    if request.method == 'POST' and 'upload_file' in request.POST:
        form = TimetableUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            batch = form.cleaned_data['batch']
            
            parser = TimetableParser()
            success, message = parser.parse_excel(excel_file, request.user, batch)
            
            if success:
                update_attendance_stats(request.user)
                return redirect('attendance')
            else:
                return render(request, 'home/attendance.html', {
                    'form': form, 'error': message, 'has_timetable': False
                })

    # Logic C: Mark Attendance
    if request.method == 'POST' and 'session_id' in request.POST:
        session_id = request.POST.get('session_id')
        status = request.POST.get('status')
        session = get_object_or_404(AttendanceSession, id=session_id, user=request.user)
        session.status = status
        session.save()
        update_attendance_stats(request.user)
        return redirect('attendance')

    # Logic D: Display
    has_timetable = Subject.objects.filter(user=request.user).exists()
    
    if not has_timetable:
        return render(request, 'home/attendance.html', {
            'form': TimetableUploadForm(), 'has_timetable': False
        })

    todays_sessions = AttendanceSession.objects.filter(user=request.user, date=today).order_by('id')
    subjects = Subject.objects.filter(user=request.user)
    
    context = {
        'has_timetable': True,
        'todays_sessions': todays_sessions,
        'subjects': subjects,
        'today_date': today.strftime("%A, %d %B %Y"),
    }
    return render(request, 'home/attendance.html', context)

# ==========================================
# 📚 LIBRARY & SUBJECTS (UPDATED)
# ==========================================

@login_required(login_url='login')
def library_view(request):
    # 🟢 UPDATE: Filter to show ONLY Theory subjects
    subjects = Subject.objects.filter(user=request.user, is_theory=True)
    
    # Check if a specific folder is selected
    selected_subject_id = request.GET.get('subject_id')
    selected_subject = None
    notes = []

    if selected_subject_id:
        selected_subject = get_object_or_404(Subject, id=selected_subject_id, user=request.user)
        notes = AINote.objects.filter(user=request.user, subject=selected_subject).order_by('-created_at')
    else:
        # Show "Unsorted" notes (notes with no subject)
        notes = AINote.objects.filter(user=request.user, subject__isnull=True).order_by('-created_at')

    return render(request, 'home/library.html', {
        'subjects': subjects,
        'selected_subject': selected_subject,
        'notes': notes
    })

@login_required
def add_subject(request):
    if request.method == 'POST':
        name = request.POST.get('subject_name')
        if name:
            # 🟢 UPDATE: Explicitly set is_theory=True for manual folders
            Subject.objects.create(
                user=request.user, 
                name=name, 
                code=name[:3].upper(),
                is_theory=True
            )
    return redirect('library')

# ==========================================
# 🤖 AI NOTES (UPDATED LOGIC)
# ==========================================

@login_required(login_url='login')
def ai_notes(request):
    summary = None
    raw_text = None
    error = None
    
    # 🟢 UPDATE: Dropdown only shows Theory subjects
    subjects = Subject.objects.filter(user=request.user, is_theory=True)

    # 1. Check if user is viewing an OLD note (from Library)
    note_id = request.GET.get('note_id')
    if note_id:
        saved_note = get_object_or_404(AINote, id=note_id, user=request.user)
        summary = saved_note.content_html
        raw_text = saved_note.raw_text

    if request.method == 'POST':
        # 2. CASE A: User clicked "Save Note" button
        if 'save_note' in request.POST:
            title = request.POST.get('title')
            content = request.POST.get('content')
            raw = request.POST.get('raw')
            subject_id = request.POST.get('subject_id')
            
            # Find the subject object if selected
            subject_obj = None
            if subject_id:
                subject_obj = Subject.objects.get(id=subject_id)
                
            # Create the permanent note
            AINote.objects.create(
                user=request.user,
                title=title,
                subject=subject_obj,
                content_html=content,
                raw_text=raw
            )
            # Redirect to the specific folder view in Library
            if subject_obj:
                return redirect(f'/library/?subject_id={subject_obj.id}')
            else:
                return redirect('library')

        # 3. CASE B: User Uploaded a File
        elif 'document' in request.FILES:
            uploaded_file = request.FILES['document']
            if uploaded_file.size > 10 * 1024 * 1024:
                error = "File too large. Max 10MB."
            else:
                result, text_content = generate_notes(uploaded_file)
                if result.startswith("❌"):
                    error = result
                else:
                    summary = result
                    raw_text = text_content
                    # We DO NOT save yet. We render the page so user can Review & Save.

    return render(request, 'home/ai_notes.html', {
        'summary': summary, 
        'raw_text': raw_text, 
        'error': error,
        'subjects': subjects,
        'filename': request.FILES['document'].name if request.FILES.get('document') else "My Note"
    })

# ==========================================
# 🧠 DEEP DIVE API
# ==========================================

@csrf_exempt
def deep_dive_view(request):
    """
    API Endpoint called by JavaScript when 'Deep Dive' button is clicked.
    Returns a detailed explanation of a specific topic.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            topic = data.get('topic')
            full_text = data.get('full_text')
            
            if not topic or not full_text:
                return JsonResponse({'error': 'Missing data'}, status=400)

            # Call AI for the specific topic
            detailed_note = generate_deep_dive(topic, full_text)
            
            return JsonResponse({'detail': detailed_note})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)


<<<<<<< HEAD

# --- 7. PROFILE VIEW ---
@login_required(login_url='login')
def profile_view(request):
    # Fetch the profile to display stats like attendance %
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': profile,
    }
    return render(request, 'home/profile.html', context)
=======
    return render(request, 'home/formula_sheet.html', {
        'formulas': formulas,
        'error': error
    })
>>>>>>> parent of 48e56f0 (added profile page)
