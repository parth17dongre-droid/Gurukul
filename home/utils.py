import pandas as pd
import datetime
import re
from .models import Subject, AttendanceSession

class TimetableParser:
    def parse_excel(self, file, user, batch):
        try:
            # 1. Read Excel
            df = pd.read_excel(file, header=None)
            
            # Forward fill 'Day' column
            df.iloc[:, 0] = df.iloc[:, 0].ffill()
            df = df.fillna("-")
            
            weekly_schedule = {}
            
            # 2. Iterate Rows
            for index, row in df.iterrows():
                raw_day = str(row[0]).strip().upper()
                day_name = self.normalize_day(raw_day)
                
                if day_name:
                    if day_name not in weekly_schedule:
                        weekly_schedule[day_name] = []
                    
                    # 3. Process Cells
                    for cell_text in row[1:]:
                        clean_text = str(cell_text).strip()
                        
                        # SKIP EMPTY OR JUNK CELLS
                        if len(clean_text) < 3 or clean_text == "-": 
                            continue
                            
                        # EXTRACT LOGIC
                        final_subject = self.extract_subject(clean_text, batch)
                        
                        if final_subject:
                            weekly_schedule[day_name].append(final_subject)

            # 4. Save to DB
            self.create_db_sessions(user, weekly_schedule)
            return True, "Schedule generated!"

        except Exception as e:
            return False, str(e)

    def normalize_day(self, text):
        days = {"MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday", 
                "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday"}
        for key, val in days.items():
            if key in text: return val
        return None

    def extract_subject(self, text, user_batch):
        """
        Aggressively filters out Lunch/ELH and finds the specific batch line.
        """
        # 1. THE IGNORE LIST (Case Insensitive)
        # If the cell contains ANY of these, we kill it immediately.
        junk_keywords = ["LUNCH", "ELH", "MENTOR", "BREAK", "TEA", "RECESS"]
        
        # 2. Split cell into lines (handle both \n and / separators)
        lines = text.replace('/', '\n').split('\n')
        
        valid_lines = []
        
        # Regex to detect IF a line is batch-specific (e.g. "A1:", "B2", "CSE-C1")
        # Looks for things like "A1", "B2", "C3" surrounded by spaces or punctuation
        batch_pattern = re.compile(r"\b[A-C][1-4]\b", re.IGNORECASE)

        for line in lines:
            line = line.strip()
            upper_line = line.upper()
            
            # A. Check for Junk
            if any(junk in upper_line for junk in junk_keywords):
                continue
            
            # B. Check if line has ANY batch mentioned
            if batch_pattern.search(line):
                # Only keep if it matches OUR batch (e.g. "B2")
                # We check if user_batch ("B2") is inside the line ("CSE B2: Lab")
                if user_batch.upper() in upper_line:
                    # Clean the name: Remove "CSE B2:" prefix to just get "Lab"
                    clean_name = re.sub(r"^.*" + re.escape(user_batch) + r"[:\s-]*", "", line, flags=re.IGNORECASE)
                    valid_lines.append(clean_name.strip())
            else:
                # C. No batch mentioned? It's a common lecture (Keep it)
                if len(line) > 2:
                    valid_lines.append(line)

        if not valid_lines:
            return None
            
        return " & ".join(valid_lines)

    def create_db_sessions(self, user, weekly_schedule):
        AttendanceSession.objects.filter(user=user).delete()
        Subject.objects.filter(user=user).delete()
        
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(days=120)
        
        curr = start_date
        while curr <= end_date:
            day_name = curr.strftime("%A")
            if day_name in weekly_schedule:
                for sub_name in weekly_schedule[day_name]:
                    subject, _ = Subject.objects.get_or_create(user=user, name=sub_name)
                    AttendanceSession.objects.create(
                        user=user, subject=subject, date=curr, status='Pending'
                    )
            curr += datetime.timedelta(days=1)

# Keep the stats updater as is
def update_attendance_stats(user):
    subjects = Subject.objects.filter(user=user)
    total_sessions_overall = 0
    total_present_overall = 0
    
    for sub in subjects:
        sessions = AttendanceSession.objects.filter(user=user, subject=sub).exclude(status='Pending')
        sub.total_lectures = sessions.count()
        sub.lectures_attended = sessions.filter(status='Present').count()
        sub.save()
        total_sessions_overall += sub.total_lectures
        total_present_overall += sub.lectures_attended

    try:
        profile = user.studentprofile
        if total_sessions_overall > 0:
            profile.attendance_percentage = round((total_present_overall / total_sessions_overall) * 100, 1)
        else:
            profile.attendance_percentage = 0.0
        profile.save()
    except:
        pass