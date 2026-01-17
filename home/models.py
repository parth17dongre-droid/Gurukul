from django.db import models
from django.contrib.auth.models import User

# 1. Profile (Keeps your original fields)
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    college_name = models.CharField(max_length=100, default="SIT Pune")
    branch = models.CharField(max_length=50, default="CSE")
    current_year = models.IntegerField(default=1)
    attendance_percentage = models.FloatField(default=0.0)
    target_cgpa = models.FloatField(default=9.0)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# 2. Subject (Keeps your original fields + Adds Stats Logic)
class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    is_lab = models.BooleanField(default=False)
    
    # --- NEW FIELDS FOR STATS (Needed for the tracker) ---
    total_lectures = models.IntegerField(default=0)
    lectures_attended = models.IntegerField(default=0)
    
    # --- MATH HELPER (Calculates % on the fly) ---
    @property
    def attendance_percentage(self):
        if self.total_lectures == 0:
            return 0.0
        return round((self.lectures_attended / self.total_lectures) * 100, 1)

    def __str__(self):
        return self.name

# 3. Attendance Session (No changes needed, just standardized)
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
        ordering = ['date']

    def __str__(self):
        return f"{self.subject.name} on {self.date}"