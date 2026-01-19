import os
from groq import Groq
import PyPDF2
from pptx import Presentation
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# 🔑 CONFIGURATION
# ==========================================
current_file = Path(__file__).resolve()
project_dir = current_file.parent.parent
search_paths = [project_dir / '.env', project_dir.parent / '.env', current_file.parent / '.env']

env_path = None
for path in search_paths:
    if path.exists():
        env_path = path
        break

if env_path:
    load_dotenv(env_path)

api_key = os.getenv("GROQ_API_KEY")

# ==========================================
# 📄 FILE PROCESSING
# ==========================================
def extract_text_from_pdf(file_obj):
    try:
        reader = PyPDF2.PdfReader(file_obj)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"PDF Error: {e}")
        return None

def extract_text_from_ppt(file_obj):
    try:
        prs = Presentation(file_obj)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text
    except Exception as e:
        print(f"PPT Error: {e}")
        return None

# ==========================================
# 🧠 AI FUNCTIONS
# ==========================================

def generate_notes(uploaded_file):
    """
    Returns a TUPLE: (HTML_Summary, Raw_Text)
    We need the Raw_Text to perform the 'Deep Dives' later.
    """
    if not api_key:
        return "❌ Error: GROQ_API_KEY not found.", ""

    # 1. Extract Text
    filename = uploaded_file.name.lower()
    text = ""
    
    if filename.endswith('.pdf'):
        text = extract_text_from_pdf(uploaded_file)
    elif filename.endswith('.pptx') or filename.endswith('.ppt'):
        text = extract_text_from_ppt(uploaded_file)
    else:
        return "❌ Error: Unsupported file format.", ""

    if not text or len(text) < 50:
        return "❌ Error: Could not extract text.", ""

    # 2. Call Groq API (Initial Summary)
    try:
        client = Groq(api_key=api_key)
        truncated_text = text[:50000] # 50k char limit

        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise academic analyst. Output HTML only."
                },
                {
                    "role": "user",
                    "content": f"""
                    Analyze this text. Structure the output as follows:

                    1. Break into SUBTOPICS.
                    2. For each subtopic, use an <h3> tag with the specific Topic Name.
                    3. Under the <h3>, provide a bulleted summary <ul>.
                    4. End with a 🏁 Final Summary paragraph.

                    Example Format:
                    <h3>📌 [Topic Name]</h3>
                    <ul><li>Point 1</li></ul>
                    <hr>

                    TEXT:
                    {truncated_text}
                    """
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        
        # RETURN BOTH!
        return completion.choices[0].message.content, truncated_text

    except Exception as e:
        return f"❌ AI Error: {str(e)}", ""


def generate_deep_dive(topic, full_text):
    """
    Generates a detailed explanation for a SPECIFIC topic using the full context.
    """
    if not api_key:
        return "Error: API Key missing."

    try:
        client = Groq(api_key=api_key)
        
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict academic tutor. You provide exhaustive, detailed explanations."
                },
                {
                    "role": "user",
                    "content": f"""
                    CONTEXT:
                    {full_text}
                    
                    TASK:
                    The student has requested a "Deep Dive" on the specific topic: "{topic}".
                    
                    INSTRUCTIONS:
                    1. Reread the Context and find EVERYTHING related to "{topic}".
                    2. Explain it in extreme detail. Do not leave out any nuance, formula, or figure mentioned in the text.
                    3. If there are steps, list them. If there is a table described, format it as HTML.
                    4. Use simple HTML (<p>, <ul>, <strong>, <table>).
                    
                    OUTPUT:
                    Provide ONLY the detailed explanation.
                    """
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"
# ... (existing imports and functions)

def generate_formula_sheet(uploaded_file):
    """
    Extracts ONLY formulas, theorems, and constants from a document.
    """
    if not api_key:
        return "❌ Error: API Key missing."

    # Reuse the existing text extraction logic
    filename = uploaded_file.name.lower()
    text = ""
    
    if filename.endswith('.pdf'):
        text = extract_text_from_pdf(uploaded_file)
    elif filename.endswith('.pptx') or filename.endswith('.ppt'):
        text = extract_text_from_ppt(uploaded_file)
    else:
        return "❌ Error: Unsupported file format."

    if not text or len(text) < 50:
        return "❌ Error: Could not extract text."

    try:
        client = Groq(api_key=api_key)
        truncated_text = text[:50000]

        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a Mathematician. Your goal is to create a Formula Cheatsheet. Output HTML only."
                },
                {
                    "role": "user",
                    "content": f"""
                    Scan the following text and extract every Mathematical Formula, Theorem, and Physical Constant.
                    
                    INSTRUCTIONS:
                    1. Group them logically (e.g., "Derivatives", "Integrals", "Trigonometry").
                    2. Use HTML <table> or lists for clean formatting.
                    3. For actual math equations, use readable formatting (e.g., "a^2 + b^2 = c^2" or bold variables). 
                       *Do not use complex LaTeX like $$, just clean standard text or HTML entities.*
                    4. IGNORE long paragraphs of explanation. Only keep the math.
                    
                    REQUIRED OUTPUT FORMAT:
                    <h3>📐 [Section Name]</h3>
                    <table border="1" style="width:100%; border-collapse: collapse; margin-bottom: 20px; border-color: #4b5563;">
                        <tr style="background: rgba(255,255,255,0.1);">
                            <th style="padding: 10px;">Name/Context</th>
                            <th style="padding: 10px;">Formula</th>
                        </tr>
                        <tr>
                            <td style="padding: 10px;">Pythagoras</td>
                            <td style="padding: 10px; font-family: monospace; font-size: 1.1em;">a² + b² = c²</td>
                        </tr>
                    </table>

                    TEXT:
                    {truncated_text}
                    """
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"❌ AI Error: {str(e)}"