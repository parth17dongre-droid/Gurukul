from django import forms
from django.contrib.auth.models import User
from .models import StudentProfile

class SignUpForm(forms.ModelForm):
    # 1. Define all the fields we need
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'Last Name'}))
    username = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'Username'}))
    email = forms.EmailField(max_length=254, required=True, widget=forms.EmailInput(attrs={'class': 'glass-input', 'placeholder': 'Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'glass-input', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'glass-input', 'placeholder': 'Confirm Password'}))

    # 🟢 CRITICAL FIX: Use Integers (1, 2, 3) for the database value
    YEAR_CHOICES = [
        (1, 'First Year'),
        (2, 'Second Year'),
        (3, 'Third Year'),
        (4, 'Fourth Year'),
    ]
    
    current_year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        widget=forms.Select(attrs={'class': 'glass-input'})
    )

    BATCH_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'), ('A4', 'A4'),
        ('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3'), ('B4', 'B4'),
        ('C1', 'C1'), ('C2', 'C2'), ('C3', 'C3'), ('C4', 'C4'),
    ]
    
    batch = forms.ChoiceField(
        choices=BATCH_CHOICES,
        widget=forms.Select(attrs={'class': 'glass-input'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data

    def save(self, commit=True):
        # 1. Save the User first
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        
        if commit:
            user.save()
            # 2. Create the Student Profile with the extra data
            StudentProfile.objects.create(
                user=user,
                current_year=self.cleaned_data['current_year'], # This will now be 1, 2, 3, or 4
                batch=self.cleaned_data['batch']
            )
        return user

class TimetableUploadForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'glass-input'}))
    batch = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'glass-input', 'placeholder': 'Enter Batch (e.g. B2)'}))