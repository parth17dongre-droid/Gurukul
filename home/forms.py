from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email'] # We ask for Username and Email

    # This adds your specific CSS classes to the inputs
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'glass-input', 
                'placeholder': field.capitalize()
            })
class TimetableUploadForm(forms.Form):
    file = forms.FileField()
    batch = forms.CharField(max_length=10, label="Your Batch (e.g., A1, B2)")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'class': 'glass-input'})
        self.fields['batch'].widget.attrs.update({'class': 'glass-input', 'placeholder': 'Enter Batch (e.g., A1)'})