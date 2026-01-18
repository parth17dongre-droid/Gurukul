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
        # 🟢 UPDATED: Removed the "i > 15" break to read the FULL file
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
# 🧠 GROQ AI GENERATOR
# ==========================================
def generate_notes(uploaded_file):
    if not api_key:
        return "❌ Error: GROQ_API_KEY not found in .env file."

    # 1. Extract Text
    filename = uploaded_file.name.lower()
    text = ""
    
    if filename.endswith('.pdf'):
        text = extract_text_from_pdf(uploaded_file)
    elif filename.endswith('.pptx') or filename.endswith('.ppt'):
        text = extract_text_from_ppt(uploaded_file)
    else:
        return "❌ Error: Unsupported file format. Please upload PDF or PPTX."

    if not text or len(text) < 50:
        return "❌ Error: Could not extract text. File might be purely images."

    # 🔍 DEBUG: Print the length to the terminal so we KNOW it read everything
    print(f"🔍 DEBUG: Extracted {len(text)} characters from {filename}")

    # 2. Call Groq API
    try:
        client = Groq(api_key=api_key)
        
        # 🟢 UPDATED: Increased limit to 50,000 characters (approx 12k tokens)
        # This is safe for Llama 3 on Groq and fits huge lectures.
        truncated_text = text[:50000]

        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """
                    You are a precise academic analyst. 
                    Your job is to deconstruct complex documents into structured, point-wise notes.
                    Output MUST be pure HTML (no markdown).
                    """
                },
                {
                    "role": "user",
                    "content": f"""
                    Analyze the provided text and structure the output exactly as follows:

                    --------------------------------------------------
                    INSTRUCTIONS:
                    1. IDENTIFY SUBTOPICS: Break the text into its natural sections (e.g., "Introduction", "Methodology", "Key Arguments").
                    2. POINT-WISE SUMMARY: For *each* subtopic, provide a bulleted list (<ul>) of the core facts. Do NOT use paragraphs for these parts.
                    3. JARGON BUSTER: Extract 3-5 complex technical terms or keywords and define them simply.
                    4. FINAL VERDICT: A 2-3 sentence paragraph wrapping up the entire document.
                    --------------------------------------------------

                    REQUIRED HTML OUTPUT FORMAT:

                    <h3>📌 [Insert Subtopic Name Here]</h3>
                    <ul>
                        <li>Key point about this subtopic...</li>
                        <li>Another critical detail...</li>
                        <li>Data or specific fact...</li>
                    </ul>
                    <hr>

                    <h3>📚 Jargon Buster</h3>
                    <ul>
                        <li><strong>[Keyword 1]:</strong> Simple definition.</li>
                        <li><strong>[Keyword 2]:</strong> Simple definition.</li>
                    </ul>
                    <hr>

                    <h3>🏁 Final Summary</h3>
                    <p>
                        [Write a cohesive 2-3 sentence paragraph summarizing the main thesis or conclusion of the entire document here.]
                    </p>

                    --------------------------------------------------
                    TEXT TO ANALYZE:
                    {truncated_text}
                    """
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        return completion.choices[0].message.content

    except Exception as e:
        return f"❌ AI Error: {str(e)}"