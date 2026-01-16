from django.db import models
from django.contrib.auth.models import User

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Fields for the dashboard
    college_name = models.CharField(max_length=100, default="SIT Pune")
    branch = models.CharField(max_length=50, default="CSE")
    current_year = models.IntegerField(default=1)
    attendance_percentage = models.FloatField(default=0.0)
    target_cgpa = models.FloatField(default=9.0)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"