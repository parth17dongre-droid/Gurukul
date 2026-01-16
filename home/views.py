from django.shortcuts import render, redirect
# 1. These imports are needed for Login/Logout to work
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

# 2. These imports are needed for your Database and Forms
from .models import StudentProfile
from .forms import SignUpForm  # Ensure forms.py exists!

# --- 1. LANDING PAGE ---
def index(request):
    return render(request, 'home/index.html')

# --- 2. SIGN UP VIEW ---
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after signup
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    
    return render(request, 'home/signup.html', {'form': form})

# --- 3. LOGIN VIEW ---
def login_view(request):
    # Smart Check: If already logged in, go straight to dashboard
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
    request.session.flush() # Clears the session completely so they are truly logged out
    return redirect('index')

# --- 5. DASHBOARD VIEW ---
@login_required(login_url='login')
def dashboard(request):
    # Get or create the profile to avoid crashes
    profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    context = {
        'profile': profile
    }
    return render(request, 'home/dashboard.html', context)