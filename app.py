import os
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
import textract

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'txt'}

# Define over 30 job profiles related to software development with associated keywords
job_profile_keywords = {
    "Frontend Developer": ["HTML", "CSS", "JavaScript", "React", "Angular", "Vue", "TypeScript", "SASS", "Bootstrap"],
    "Backend Developer": ["Python", "Java", "Node.js", "SQL", "REST APIs", "Django", "Flask", "Express.js", "C#", ".NET"],
    "Full Stack Developer": ["HTML", "CSS", "JavaScript", "React", "Angular", "Python", "Django", "Node.js", "MongoDB", "SQL"],
    "Mobile App Developer": ["Swift", "Kotlin", "Java", "React Native", "Flutter", "Objective-C", "Xamarin"],
    "DevOps Engineer": ["Docker", "Kubernetes", "Jenkins", "AWS", "Azure", "CI/CD", "Ansible", "Terraform"],
    "Software Engineer": ["C++", "Java", "Python", "OOP", "Data Structures", "Algorithms", "Git", "Linux"],
    "Cloud Solutions Developer": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Microservices", "Serverless"],
    "Data Engineer": ["SQL", "Python", "Apache Spark", "Hadoop", "ETL", "Data Warehousing", "Big Data"],
    "Machine Learning Engineer": ["Python", "TensorFlow", "PyTorch", "scikit-learn", "Deep Learning", "Data Analysis"],
    "AI Developer": ["Python", "TensorFlow", "PyTorch", "NLP", "Computer Vision", "Deep Learning"],
    "Security Software Engineer": ["Cybersecurity", "Encryption", "Penetration Testing", "Network Security", "Firewalls"],
    "Embedded Systems Developer": ["C", "C++", "Microcontrollers", "RTOS", "Hardware", "IoT"],
    "Quality Assurance Engineer": ["Testing", "Selenium", "JUnit", "Automated Testing", "Manual Testing", "Bug Tracking"],
    "Test Automation Engineer": ["Selenium", "Python", "Java", "Automated Testing", "CI/CD", "Jenkins"],
    "Systems Engineer": ["Linux", "Networking", "Scripting", "Automation", "Systems Integration"],
    "Database Developer": ["SQL", "NoSQL", "Database Design", "Oracle", "MySQL", "PostgreSQL"],
    "Blockchain Developer": ["Blockchain", "Ethereum", "Smart Contracts", "Solidity", "Cryptography"],
    "IoT Developer": ["IoT", "Embedded Systems", "Python", "C", "Networking", "Sensors"],
    "Game Developer": ["C++", "C#", "Unity", "Unreal Engine", "Game Design", "3D Modeling"],
    "AR/VR Developer": ["Unity", "Unreal Engine", "C#", "3D Modeling", "Augmented Reality", "Virtual Reality"],
    "API Developer": ["REST APIs", "GraphQL", "Node.js", "Python", "Java", "Microservices"],
    "Site Reliability Engineer (SRE)": ["Linux", "Python", "Monitoring", "CI/CD", "Automation", "Cloud"],
    "Software Architect": ["Design Patterns", "System Architecture", "Microservices", "Scalability", "Java", "C#"],
    "Integration Engineer": ["API Integration", "Middleware", "Java", "C#", "System Integration"],
    "CI/CD Engineer": ["Jenkins", "GitLab", "CI/CD", "Docker", "Automation"],
    "Frontend Engineer": ["HTML", "CSS", "JavaScript", "React", "Vue", "Responsive Design"],
    "Backend Engineer": ["Python", "Java", "Node.js", "SQL", "REST APIs", "Microservices"],
    "Software Development Manager": ["Project Management", "Agile", "Scrum", "Team Leadership", "Communication"],
    "Solutions Architect": ["System Architecture", "Cloud", "Microservices", "Design Patterns", "Scalability"],
    "Automation Engineer": ["Automation", "Selenium", "Python", "Test Automation", "CI/CD"]
}

def allowed_file(filename):
    """Check if the file has one of the allowed extensions."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    """
    Extract text using textract (supports PDF, DOC, and TXT files).
    Returns the extracted text or an empty string on error.
    """
    try:
        text = textract.process(file_path)
        return text.decode('utf-8')
    except Exception as e:
        print("Error extracting text:", e)
        return ""

def analyze_resume(resume_text, job_profile):
    """
    Compare the resume text with the selected job profile's keywords.
    Returns a dictionary with a match score, list of matched skills, and missing skills.
    """
    keywords = job_profile_keywords[job_profile]
    resume_text_lower = resume_text.lower()
    matches = [kw for kw in keywords if kw.lower() in resume_text_lower]
    missing = [kw for kw in keywords if kw.lower() not in resume_text_lower]
    score = (len(matches) / len(keywords)) * 100 if keywords else 0
    return {
        "score": round(score, 2),
        "matches": matches,
        "missing": missing,
        "total_keywords": len(keywords)
    }

@app.route('/', methods=['GET', 'POST'])
def upload_resume():
    if request.method == 'POST':
        # Check if a resume file is provided
        if 'resume' not in request.files:
            flash("No resume file part in the request.")
            return redirect(request.url)
        file = request.files['resume']
        if file.filename == "":
            flash("No file selected.")
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash("Unsupported file type. Please upload a PDF, DOC, or TXT file.")
            return redirect(request.url)
        
        # Get the selected job profile from the form
        selected_profile = request.form.get('job_profile')
        if selected_profile not in job_profile_keywords:
            flash("Invalid job profile selected.")
            return redirect(request.url)
        
        # Save the file securely
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Extract text from the uploaded resume
        resume_text = extract_text_from_file(file_path)
        
        # Analyze the resume against the selected job profile's keywords
        analysis = analyze_resume(resume_text, selected_profile)
        
        return render_template('result.html', result=analysis, profile=selected_profile)
    
    # Render the upload form, passing the list of job profiles to the template
    return render_template('upload.html', job_profiles=list(job_profile_keywords.keys()))

if __name__ == '__main__':
    # Ensure the uploads folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
