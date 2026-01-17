import pandas as pd
import datetime
import re
from .models import Subject, AttendanceSession

class TimetableParser:
    def parse_excel(self, file, user, batch):
        try:
            print(f"\n🚀 STARTING LAB-TAGGED PARSE FOR BATCH: {batch}")
            
            # 1. READ ALL SHEETS
            try:
                all_sheets = pd.read_excel(file, header=None, sheet_name=None)
            except Exception as e:
                return False, f"Could not read Excel file. Error: {str(e)}"
            
            # 2. SELECT THE CORRECT SHEET
            target_section = batch[0].upper() # "B" from "B2"
            target_df = None
            found_sheet_name = ""

            for name, df in all_sheets.items():
                norm_name = name.upper().replace(" ", "")
                if "CSE" in norm_name and target_section in norm_name:
                    target_df = df
                    found_sheet_name = name
                    print(f"   ✅ Found Correct Sheet: '{name}'")
                    break
            
            # Fallback
            if target_df is None:
                for name, df in all_sheets.items():
                    if name.upper().strip().endswith(target_section):
                        target_df = df
                        found_sheet_name = name
                        print(f"   ⚠️ Fallback Sheet: '{name}'")
                        break
            
            if target_df is None:
                return False, f"Could not find a worksheet for Section '{target_section}'."

            # ==========================================
            # 3. PROCESS THE SHEET
            # ==========================================
            df = target_df
            weekly_schedule = {}

            # --- A. SMART ANCHOR ---
            start_row_index = -1
            day_col_index = 0
            found_anchor = False
            
            for r in range(min(25, len(df))):
                for c in range(min(10, len(df.columns))):
                    cell_val = str(df.iat[r, c]).strip().upper()
                    if "MON" in cell_val:
                        start_row_index = r
                        day_col_index = c
                        found_anchor = True
                        break
                if found_anchor: break
            
            if not found_anchor:
                return False, f"Could not find 'Monday' in sheet '{found_sheet_name}'."

            # --- B. CROP & PREPARE ---
            df = df.iloc[start_row_index:, day_col_index:].reset_index(drop=True)
            df.iloc[:, 0] = df.iloc[:, 0].ffill().fillna("")
            
            # --- C. ITERATE ROWS ---
            for index, row in df.iterrows():
                raw_day = str(row.iloc[0]).strip().upper()
                day_name = self.normalize_day(raw_day)
                
                if not day_name: continue

                if day_name not in weekly_schedule:
                    weekly_schedule[day_name] = []

                # Iterate Columns
                for cell_text in row.iloc[1:]:
                    cell_text = str(cell_text).strip()
                    if len(cell_text) < 2 or cell_text == "nan": continue

                    # --- D. SPLIT & CLEAN ---
                    parts = re.split(r'[\n/]', cell_text)
                    
                    for part in parts:
                        part = part.strip()
                        if len(part) < 2: continue
                        
                        # LOGIC: Keep or Skip?
                        final_subject = self.process_part(part, batch)
                        
                        if final_subject and len(final_subject) > 1:
                            if final_subject not in weekly_schedule[day_name]:
                                print(f"      🔹 ADDED: {final_subject} ({day_name})")
                                weekly_schedule[day_name].append(final_subject)

            # 4. SAVE TO DATABASE
            self.create_db_sessions(user, weekly_schedule)
            return True, f"Success! Loaded schedule from '{found_sheet_name}'."

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False, f"Processing Error: {str(e)}"

    def normalize_day(self, text):
        days = {"MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday", 
                "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday"}
        for key, val in days.items():
            if key in text: return val
        return None

    def process_part(self, text, user_batch):
        # 1. Junk Filter
        junk_keywords = ["LUNCH", "ELH", "MENTOR", "BREAK", "TEA", "RECESS", "TIME", "SATURDAY"]
        if any(junk in text.upper() for junk in junk_keywords):
            return None

        # 2. Setup Regex
        raw_upper = text.upper()
        my_batch_clean = user_batch.upper().replace(" ", "") # "B2"
        other_batch_pattern = re.compile(r"\b[A-C][\s\-]?[1-4]\b", re.IGNORECASE)

        # --- DECISION LOGIC ---

        # A. LAB DETECTION (Explicitly MY batch)
        if my_batch_clean in raw_upper.replace(" ", "").replace("-", ""):
            # Clean the name first
            clean = self.clean_name(text, user_batch)
            if not clean: return None
            
            # TAG IT AS LAB (if not already there)
            if "LAB" not in clean.upper():
                return f"{clean} LAB"
            return clean

        # B. OTHER BATCH (Skip)
        match = other_batch_pattern.search(text)
        if match:
            return None 

        # C. THEORY (No Batch)
        return self.clean_name(text, "")

    def clean_name(self, text, batch):
        # 1. Slice after batch name
        if batch:
            match = re.search(re.escape(batch), text, re.IGNORECASE)
            if match: text = text[match.end():]
        
        # 2. Remove brackets (...)
        text = re.sub(r'\s*\(.*?\)', '', text)
        
        # 3. Cleanup junk
        text = text.replace(':', '').replace('-', '').replace('CSE', '').replace('IT', '').strip()
        
        # 4. Final check
        if len(text) < 2: return None
        return text

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

# --- STATS UPDATER ---
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