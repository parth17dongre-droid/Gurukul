from django.db import models
from django.contrib.auth.models import User

# 1. Profile (You already have this)
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    college_name = models.CharField(max_length=100, default="SIT Pune")
    branch = models.CharField(max_length=50, default="CSE")
    current_year = models.IntegerField(default=1)
    attendance_percentage = models.FloatField(default=0.0)
    target_cgpa = models.FloatField(default=9.0)
    
    def __str__(self):
        return self.user.username

# 2. Subject (e.g., "Data Structures", "Calculus")
class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    is_lab = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

# 3. Attendance Session (A specific class on a specific date)
# This replaces your 'sessions' table in the old code
class AttendanceSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(
        max_length=20, 
        choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Pending', 'Pending')],
        default='Pending'
    )

    class Meta:
        ordering = ['date'] # Sort by date automatically

    def __str__(self):
        return f"{self.subject.name} on {self.date}"