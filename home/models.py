from django.db import models
from django.contrib.auth.models import User

# 1. Profile
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Existing fields causing the current error
    college_name = models.CharField(max_length=100, default="SIT Pune")
    branch = models.CharField(max_length=50, default="CSE")
    current_year = models.IntegerField(default=1)
    
    # 🟢 NEW FIELDS (Required for the Profile Page feature)
    semester = models.CharField(max_length=50, default="Not Set")
    batch = models.CharField(max_length=20, default="--")
    
    # Stats
    attendance_percentage = models.FloatField(default=0.0)
    target_cgpa = models.FloatField(default=9.0)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# 2. Subject
class Subject(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    is_lab = models.BooleanField(default=False)
    is_theory = models.BooleanField(default=True)

    total_lectures = models.IntegerField(default=0)
    lectures_attended = models.IntegerField(default=0)
    
    @property
    def attendance_percentage(self):
        if self.total_lectures == 0:
            return 0.0
        return round((self.lectures_attended / self.total_lectures) * 100, 1)

    def __str__(self):
        return self.name

class TimetableSlot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    day = models.CharField(max_length=20)  # e.g., "MONDAY"
    time = models.CharField(max_length=50) # e.g., "10:00 - 11:00"

    def __str__(self):
        return f"{self.day}: {self.subject.name} ({self.time})"

# 3. Attendance Session
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

# 4. AI Note
class AINote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True) 
    title = models.CharField(max_length=200)
    content_html = models.TextField()
    raw_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.subject.name if self.subject else 'Unsorted'})"