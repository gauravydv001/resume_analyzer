import os
import re
from flask import Flask, request, render_template, redirect, url_for, flash
from io import BytesIO
import PyPDF2
from docx import Document
from job_profiles import job_profile_keywords  # Import job profiles

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-sec-key')

def extract_text(file_stream, extension):
    """Extract text from uploaded file."""
    try:
        if extension == 'pdf':
            pdf = PyPDF2.PdfReader(file_stream)
            return '\n'.join([page.extract_text() for page in pdf.pages])
        elif extension == 'docx':
            doc = Document(file_stream)
            return '\n'.join([para.text for para in doc.paragraphs])
        elif extension == 'txt':
            return file_stream.read().decode('utf-8')
        else:
            raise ValueError("Unsupported file type")
    except Exception as e:
        raise RuntimeError(f"Text extraction failed: {str(e)}")

def analyze_resume(text, profile):
    """Analyze resume against selected profile."""
    keywords = job_profile_keywords.get(profile, {})
    text_lower = text.lower()
    
    # Calculate matches for skills, education, experience, and certifications
    matches = {
        "skills": [kw for kw in keywords.get("skills", []) if kw.lower() in text_lower],
        "education": [kw for kw in keywords.get("education", []) if kw.lower() in text_lower],
        "experience": [kw for kw in keywords.get("experience", []) if kw.lower() in text_lower],
        "certifications": [kw for kw in keywords.get("certifications", []) if kw.lower() in text_lower]
    }
    
    # Calculate overall score
    total_keywords = sum(len(v) for v in keywords.values())
    matched_keywords = sum(len(v) for v in matches.values())
    score = (matched_keywords / total_keywords) * 100 if total_keywords > 0 else 0
    
    return {
        "score": round(score, 2),
        "matches": matches,
        "missing": {
            "skills": [kw for kw in keywords.get("skills", []) if kw.lower() not in text_lower],
            "education": [kw for kw in keywords.get("education", []) if kw.lower() not in text_lower],
            "experience": [kw for kw in keywords.get("experience", []) if kw.lower() not in text_lower],
            "certifications": [kw for kw in keywords.get("certifications", []) if kw.lower() not in text_lower]
        },
        "total_keywords": total_keywords
    }

def suggest_profiles(text, current_profile):
    """Suggest better job profiles based on resume content (top 5 only)."""
    suggestions = []
    text_lower = text.lower()
    
    for profile, keywords in job_profile_keywords.items():
        if profile == current_profile:
            continue  # Skip the current profile
        
        # Calculate match score for this profile
        matched = {
            "skills": len([kw for kw in keywords.get("skills", []) if kw.lower() in text_lower]),
            "education": len([kw for kw in keywords.get("education", []) if kw.lower() in text_lower]),
            "experience": len([kw for kw in keywords.get("experience", []) if kw.lower() in text_lower]),
            "certifications": len([kw for kw in keywords.get("certifications", []) if kw.lower() in text_lower])
        }
        total = sum(len(v) for v in keywords.values())
        score = (sum(matched.values()) / total) * 100 if total > 0 else 0
        
        suggestions.append({
            "profile": profile,
            "score": round(score, 2),
            "matches": matched
        })
    
    # Sort suggestions by score (descending) and return top 5
    return sorted(suggestions, key=lambda x: x["score"], reverse=True)[:5]

@app.route('/', methods=['GET', 'POST'])
def upload_resume():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash("No file uploaded")
            return redirect(request.url)
            
        file = request.files['resume']
        profile = request.form.get('job_profile')
        
        if not file or file.filename == '':
            flash("No file selected")
            return redirect(request.url)
            
        if not profile or profile not in job_profile_keywords:
            flash("Invalid job profile")
            return redirect(request.url)

        try:
            ext = file.filename.split('.')[-1].lower()
            text = extract_text(BytesIO(file.read()), ext)
            
            if not text.strip():
                flash("Empty file or no text found")
                return redirect(request.url)
                
            analysis = analyze_resume(text, profile)
            suggestions = []
            
            # Suggest better profiles if score is low
            if analysis["score"] < 50:
                suggestions = suggest_profiles(text, profile)
            
            return render_template('result.html',
                result=analysis,
                profile=profile,
                suggestions=suggestions)
                
        except Exception as e:
            flash(str(e))
            return redirect(request.url)
            
    return render_template('upload.html',
        profiles=list(job_profile_keywords.keys()))

if __name__ == '__main__':
    app.run()