import os
import re
import logging
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from io import BytesIO
import PyPDF2
from docx import Document
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from werkzeug.utils import secure_filename
from resource_links import get_skill_resources, get_certification_resources, get_generic_skill_link, get_generic_certification_link

# TODO: REMOVE FOR DEPLOYMENT - Start
# Debug logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# For deployment, change to:
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# TODO: REMOVE FOR DEPLOYMENT - End

class ResumeAnalyzer:
    def __init__(self):
        self.job_profile_keywords = {
            "Frontend Developer": {
                "skills": {"HTML": 3, "CSS": 3, "JavaScript": 4, "React": 5, "Angular": 4, "Vue": 4, "TypeScript": 4, "Next.js": 3, "Redux": 4},
                "education": {"B.Tech in Computer Science": 14, "BCA": 8, "M.Tech in Software Engineering": 4, "MCA": 7, "B.Sc in IT": 8, "Diploma in Web Development": 3},
                "experience": {"UI/UX": 4, "Frontend Development": 5, "Web Design": 4, "Responsive Design": 4, "Cross-Browser Compatibility": 3, "Mobile-First Development": 4},
                "certifications": {"Google UX Design": 4, "Meta Front-End Developer": 5, "Microsoft Certified: Web Developer Associate": 4, "Udacity Frontend Nanodegree": 4, "FreeCodeCamp Frontend Certification": 3},
                "seniority": {
                    "target_level": "mid",
                    "levels": {
                        "fresher": {"min_exp": 0, "max_exp": 2, "keywords": ["fresher", "junior"], "exp_weight": 0.5},
                        "mid": {"min_exp": 2, "max_exp": 5, "keywords": ["mid-level", "L2"], "exp_weight": 1.0},
                        "senior": {"min_exp": 5, "max_exp": 20, "keywords": ["senior", "lead"], "exp_weight": 1.2}
                    }
                }
            },
            
            "Full-Stack Developer": {
                "skills": {"HTML": 3, "CSS": 3, "JavaScript": 4, "React": 4, "Node.js": 5, "Express.js": 5, "Angular": 4, "MongoDB": 5, "SQL": 4, "TypeScript": 4},
                "education": {"B.Tech in Computer Science": 14, "M.Tech in Software Engineering": 4, "BCA": 8, "MCA": 7},
                "experience": {"Full-Stack Development": 5, "Backend Development": 5, "Frontend Development": 4, "API Development": 4, "Database Management": 4},
                "certifications": {"Udacity Full Stack Nanodegree": 5, "Google Cloud Professional Developer": 4, "AWS Certified Solutions Architect": 4},
                "seniority": {
                    "target_level": "mid",
                    "levels": {
                        "fresher": {"min_exp": 0, "max_exp": 2, "keywords": ["fresher", "junior"], "exp_weight": 0.5},
                        "mid": {"min_exp": 2, "max_exp": 5, "keywords": ["mid-level", "L2"], "exp_weight": 1.0},
                        "senior": {"min_exp": 5, "max_exp": 20, "keywords": ["senior", "lead"], "exp_weight": 1.2}
                    }
                }
            },
            
            "DevOps Engineer": {
                "skills": {"Linux": 5, "Docker": 5, "Kubernetes": 5, "Jenkins": 4, "Terraform": 4, "CI/CD": 5, "AWS": 4, "Azure": 4, "Git": 4, "Monitoring (Prometheus, Grafana)": 4},
                "education": {"B.Tech in Computer Science": 14, "M.Tech in Cloud Computing": 4, "BCA": 8, "MCA": 7},
                "experience": {"Infrastructure Automation": 5, "Continuous Integration": 5, "Continuous Deployment": 5, "Cloud Management": 4, "System Administration": 4},
                "certifications": {"AWS Certified DevOps Engineer": 5, "Certified Kubernetes Administrator (CKA)": 5, "Google Professional Cloud DevOps Engineer": 4, "Docker Certified Associate": 4},
                "seniority": {
                    "target_level": "mid",
                    "levels": {
                        "fresher": {"min_exp": 0, "max_exp": 2, "keywords": ["fresher", "junior"], "exp_weight": 0.5},
                        "mid": {"min_exp": 2, "max_exp": 5, "keywords": ["mid-level", "L2"], "exp_weight": 1.0},
                        "senior": {"min_exp": 5, "max_exp": 20, "keywords": ["senior", "lead"], "exp_weight": 1.2}
                    }
                }
            },

            "Software Engineer": {
                "skills": {"Java": 5, "C++": 5, "Python": 4, "JavaScript": 4, "C#": 4, "SQL": 4, "OOP": 5, "Algorithms": 5, "Data Structures": 5, "Version Control (Git)": 4},
                "education": {"B.Tech in Computer Science": 14, "M.Tech in Software Engineering": 4, "BCA": 8, "MCA": 7},
                "experience": {"Software Development": 5, "System Design": 5, "Object-Oriented Programming": 5, "Database Management": 4, "API Development": 4},
                "certifications": {"Oracle Certified Java Programmer": 5, "Microsoft Certified: Azure Developer Associate": 4, "AWS Certified Developer – Associate": 4},
                "seniority": {
                    "target_level": "mid",
                    "levels": {
                        "fresher": {"min_exp": 0, "max_exp": 2, "keywords": ["fresher", "junior"], "exp_weight": 0.5},
                        "mid": {"min_exp": 2, "max_exp": 5, "keywords": ["mid-level", "L2"], "exp_weight": 1.0},
                        "senior": {"min_exp": 5, "max_exp": 20, "keywords": ["senior", "lead"], "exp_weight": 1.2}
                    }
                }
            },

            "Database Administrator (DBA)": {
                "skills": {"SQL": 5, "MySQL": 5, "PostgreSQL": 5, "MongoDB": 4, "Oracle Database": 5, "NoSQL": 4, "Database Security": 5, "Replication": 4, "Backup and Recovery": 5, "Performance Tuning": 4},
                "education": {"B.Tech in Computer Science": 14, "M.Tech in Database Management": 4, "BCA": 8, "MCA": 7},
                "experience": {"Database Management": 5, "Database Optimization": 5, "Data Recovery": 5, "Database Security": 5, "Query Optimization": 4},
                "certifications": {"Oracle Certified Professional": 5, "Microsoft Certified: Azure Database Administrator Associate": 4, "MongoDB Certified DBA": 4},
                "seniority": {
                    "target_level": "mid",
                    "levels": {
                        "fresher": {"min_exp": 0, "max_exp": 2, "keywords": ["fresher", "junior"], "exp_weight": 0.5},
                        "mid": {"min_exp": 2, "max_exp": 5, "keywords": ["mid-level", "L2"], "exp_weight": 1.0},
                        "senior": {"min_exp": 5, "max_exp": 20, "keywords": ["senior", "lead"], "exp_weight": 1.2}
                    }
                }
            },

            "Cloud Engineer": {
                "skills": {"AWS": 5, "Azure": 5, "Google Cloud": 5, "Terraform": 4, "Docker": 4, "Kubernetes": 4, "Cloud Migration": 5, "Automation": 5, "Networking": 4, "Security": 4},
                "education": {"B.Tech in Computer Science": 14, "M.Tech in Cloud Computing": 4, "MCA": 7, "BCA": 8},
                "experience": {"Cloud Infrastructure": 5, "Cloud Deployment": 5, "Cloud Security": 4, "Cloud Automation": 4},
                "certifications": {"AWS Certified Solutions Architect": 5, "Google Cloud Professional Cloud Architect": 5, "Microsoft Certified: Azure Solutions Architect Expert": 4},
                "seniority": {
                    "target_level": "mid",
                    "levels": {
                        "fresher": {"min_exp": 0, "max_exp": 2, "keywords": ["fresher", "junior"], "exp_weight": 0.5},
                        "mid": {"min_exp": 2, "max_exp": 5, "keywords": ["mid-level", "L2"], "exp_weight": 1.0},
                        "senior": {"min_exp": 5, "max_exp": 20, "keywords": ["senior", "lead"], "exp_weight": 1.2}
                    }
                }
            },

            "API Developer": {
                "skills": {"REST API": 5, "GraphQL": 4, "JSON": 4, "Node.js": 5, "Express.js": 5, "API Security": 4, "OAuth": 4, "JWT": 4, "API Testing": 4, "Swagger": 4},
                "education": {"B.Tech in Computer Science": 14, "M.Tech in Software Engineering": 4, "BCA": 8, "MCA": 7},
                "experience": {"API Design": 5, "Backend Development": 5, "Microservices": 4, "API Testing": 4},
                "certifications": {"AWS Certified Developer - Associate": 5, "Postman API Certification": 4, "Google Cloud API Management": 4},
                "seniority": {
                    "target_level": "mid",
                    "levels": {
                        "fresher": {"min_exp": 0, "max_exp": 2, "keywords": ["fresher", "junior"], "exp_weight": 0.5},
                        "mid": {"min_exp": 2, "max_exp": 5, "keywords": ["mid-level", "L2"], "exp_weight": 1.0},
                        "senior": {"min_exp": 5, "max_exp": 20, "keywords": ["senior", "lead"], "exp_weight": 1.2}
                    }
                }
            }
        }

        # Education variations mapping
        self.education_variations = {
            "MCA": ["Master in Computer Application", "Masters in Computer Application", "Master of Computer Application", "Masters of Computer Application", "M.C.A", "M.C.A.", "MCA","Masters of Computer Applications"],
            "BCA": ["Bachelor in Computer Application", "Bachelors in Computer Application", "Bachelor of Computer Application", "Bachelors of Computer Application", "B.C.A", "B.C.A.", "BCA","Bachelors of Computer Applications"],
            "B.Tech in Computer Science": ["Bachelor of Technology in Computer Science", "B.Tech Computer Science", "B.Tech CS", "B.Tech. CS", "BTech CS", "Bachelor of Technology CS"],
            "M.Tech in Software Engineering": ["Master of Technology in Software Engineering", "M.Tech Software Engineering", "M.Tech SE", "MTech SE", "Master in Software Engineering"]
        }

        # Job title variations mapping
        self.job_title_variations = {
            "Full-Stack Developer": ["Full Stack Developer", "Fullstack Developer", "Full-Stack Engineer", "Full Stack Engineer", "Software Developer Intern", "Full Stack Development Engineer"],
            "Frontend Developer": ["Front-End Developer", "Front End Developer", "Frontend Engineer", "UI Developer", "Web Frontend Developer"],
            "Software Engineer": ["Software Developer", "SDE", "Software Development Engineer", "Programming Engineer", "Software Developer Intern"]
        }
    
    def try_fuzzy_match(self, text, variations):
        """Helper method to try different fuzzy matching techniques"""
        text = text.lower().strip()
        best_ratio = 0
        best_match = None
        
        for variation in variations:
            variation = variation.lower()
            # Try different fuzzy matching methods
            ratio1 = fuzz.ratio(text, variation)  # Simple ratio
            ratio2 = fuzz.partial_ratio(text, variation)  # Partial ratio
            ratio3 = fuzz.token_sort_ratio(text, variation)  # Token sort ratio
            ratio4 = fuzz.token_set_ratio(text, variation)  # Token set ratio
            
            # Get the best ratio from all methods
            best = max(ratio1, ratio2, ratio3, ratio4)
            if best > best_ratio:
                best_ratio = best
                best_match = variation
                
        return best_ratio, best_match

    def normalize_education(self, education_text):
        """Normalize education qualification using fuzzy matching"""
        if not education_text:
            return None
            
        # TODO: REMOVE FOR DEPLOYMENT - Start
        logger.debug(f"Normalizing education text: '{education_text}'")
        # TODO: REMOVE FOR DEPLOYMENT - End
        
        education_text = education_text.lower().strip()
        
        # First try exact matches from variations
        for standard, variations in self.education_variations.items():
            for variant in variations:
                variant_lower = variant.lower()
                if variant_lower in education_text:
                    # TODO: REMOVE FOR DEPLOYMENT - Start
                    logger.debug(f"Found exact match: {standard} from variation {variant}")
                    # TODO: REMOVE FOR DEPLOYMENT - End
                    return standard
                elif education_text in variant_lower:
                    # TODO: REMOVE FOR DEPLOYMENT - Start
                    logger.debug(f"Found contained match: {standard} from variation {variant}")
                    # TODO: REMOVE FOR DEPLOYMENT - End
                    return standard
        
        # TODO: REMOVE FOR DEPLOYMENT - Start
        logger.debug("No exact match found for education text")
        # TODO: REMOVE FOR DEPLOYMENT - End
        return None

    def normalize_job_title(self, title_text):
        """Normalize job title using fuzzy matching"""
        best_match = None
        highest_ratio = 0
        
        # First try exact matches from variations
        for standard, variations in self.job_title_variations.items():
            for variant in variations:
                if variant.lower() in title_text.lower():
                    return standard
        
        # If no exact match, try fuzzy matching
        for standard, variations in self.job_title_variations.items():
            for variant in variations:
                ratio = fuzz.partial_ratio(variant.lower(), title_text.lower())
                if ratio > highest_ratio and ratio > 85:  # 85% threshold for fuzzy matching
                    highest_ratio = ratio
                    best_match = standard
        
        return best_match if best_match else title_text

    def extract_text(self, file_stream, extension):
        if extension == 'pdf':
            pdf = PyPDF2.PdfReader(file_stream)
            return '\n'.join([page.extract_text() for page in pdf.pages])
        elif extension == 'docx':
            doc = Document(file_stream)
            return '\n'.join([para.text for para in doc.paragraphs])
        elif extension == 'txt':
            return file_stream.read().decode('utf-8')
        raise ValueError("Unsupported file type")

    def detect_seniority(self, text, exp_years, profile):
        text_lower = text.lower()
        for level, cfg in profile["seniority"]["levels"].items():
            if any(kw in text_lower for kw in cfg["keywords"]):
                return level
            if cfg["min_exp"] <= exp_years <= cfg["max_exp"]:
                return level
        return "unknown"

    def analyze_all_profiles(self, text):
        results = {}
        for profile_name in self.job_profile_keywords.keys():
            try:
                analysis = self.analyze_resume(text, profile_name)
                results[profile_name] = analysis["score"]
            except Exception as e:
                logger.error(f"Error analyzing for profile {profile_name}: {str(e)}")
                continue
        return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

    def get_skill_suggestions(self, profile_name, current_skills):
        """Get suggested skills that would improve the resume"""
        profile = self.job_profile_keywords.get(profile_name)
        if not profile:
            return []
            
        # Sort skills by weight (importance)
        all_skills = sorted(profile["skills"].items(), key=lambda x: x[1], reverse=True)
        
        # Filter out skills that are already in the resume
        suggested_skills = [(skill, weight, get_skill_resources(skill) or {"video_course": get_generic_skill_link(skill)}) 
                          for skill, weight in all_skills 
                          if skill not in current_skills]
        
        # Return top 5 most important missing skills
        return suggested_skills[:5]
    
    def get_certification_suggestions(self, profile_name, current_certs):
        """Get suggested certifications that would improve the resume"""
        profile = self.job_profile_keywords.get(profile_name)
        if not profile:
            return []
            
        # Sort certifications by weight (importance)
        all_certs = sorted(profile["certifications"].items(), key=lambda x: x[1], reverse=True)
        
        # Filter out certifications that are already in the resume
        suggested_certs = [(cert, weight, get_certification_resources(cert) or {"info": get_generic_certification_link(cert)}) 
                          for cert, weight in all_certs 
                          if cert not in current_certs]
        
        # Return top 3 most relevant certifications
        return suggested_certs[:3]

    def analyze_resume(self, text, profile_name):
        # Debug logging header
        logger.debug("=" * 50)
        logger.debug("Starting resume analysis for profile: %s", profile_name)
        logger.debug("=" * 50)
        
        profile = self.job_profile_keywords.get(profile_name)
        if not profile:
            raise ValueError(f"Invalid profile: {profile_name}")
            
        text_lower = text.lower()
        
        # Experience and Seniority Analysis Debug
        logger.debug("\n[SENIORITY ANALYSIS]")
        exp_match = re.search(r'(\d+)\+?\s+years?[\s\w]*experience', text, re.IGNORECASE)
        exp_years = int(exp_match.group(1)) if exp_match else 0
        logger.debug(f"Detected experience years: {exp_years}")
        
        seniority = self.detect_seniority(text, exp_years, profile)
        target_level = profile["seniority"]["target_level"]
        exp_weight_modifier = profile["seniority"]["levels"][target_level]["exp_weight"]
        logger.debug(f"Detected seniority level: {seniority}")
        logger.debug(f"Target level: {target_level}")
        logger.debug(f"Experience weight modifier: {exp_weight_modifier}")
        
        # Experience Analysis Debug
        logger.debug("\n[EXPERIENCE ANALYSIS]")
        matched_experience = []
        for exp in profile["experience"].keys():
            if exp.lower() in text_lower:
                matched_experience.append(exp)
                logger.debug(f"✅ Found experience: {exp}")
            else:
                logger.debug(f"❌ Missing experience: {exp}")
        
        # Calculate matches
        results = {"matches": {}, "scores": {}, "totals": {}}
        
        # Skills Analysis Debug
        logger.debug("\n[SKILLS ANALYSIS]")
        matched_skills = [kw for kw in profile["skills"] if kw.lower() in text_lower]
        logger.debug("Analyzing skills matches:")
        for skill in profile["skills"].keys():
            if skill in matched_skills:
                logger.debug(f"✅ Found skill: {skill} (Weight: {profile['skills'][skill]})")
            else:
                logger.debug(f"❌ Missing skill: {skill} (Weight: {profile['skills'][skill]})")
        
        # Education Analysis Debug
        logger.debug("\n[EDUCATION ANALYSIS]")
        matched_education = set()
        text_parts = [part.strip() for part in text.split('\n') if part.strip()]
        full_text = ' '.join(text_parts).lower()
        
        # Process education matching with logging
        for standard, variations in self.education_variations.items():
            logger.debug(f"Checking education: {standard}")
            for variation in variations:
                variation_lower = variation.lower()
                if len(variation_lower.split()) <= 1:
                    continue
                
                if f" {variation_lower} " in f" {full_text} " or \
                   full_text.startswith(f"{variation_lower} ") or \
                   full_text.endswith(f" {variation_lower}") or \
                   full_text == variation_lower:
                    matched_education.add(standard)
                    logger.debug(f"✅ Matched education: {standard} from '{variation_lower}'")
                    break
                else:
                    logger.debug(f"❌ No match for variation: '{variation_lower}'")
        
        matched_education = list(matched_education)
        
        # Certification Analysis Debug
        logger.debug("\n[CERTIFICATION ANALYSIS]")
        matched_certs = [kw for kw in profile["certifications"] if kw.lower() in text_lower]
        logger.debug("Analyzing certification matches:")
        for cert in profile["certifications"].keys():
            if cert in matched_certs:
                logger.debug(f"✅ Found certification: {cert} (Weight: {profile['certifications'][cert]})")
            else:
                logger.debug(f"❌ Missing certification: {cert} (Weight: {profile['certifications'][cert]})")
        
        # Store results
        results["matches"] = {
            "education": matched_education,
            "experience": matched_experience,
            "skills": matched_skills,
            "certifications": matched_certs
        }
        
        # Calculate scores with debug logging
        logger.debug("\n[SCORE CALCULATIONS]")
        for category in ['skills', 'experience', 'certifications']:
            results["scores"][category] = sum(profile[category][kw] for kw in results["matches"][category])
            results["totals"][category] = sum(profile[category].values())
            logger.debug(f"{category.title()} score: {results['scores'][category]}/{results['totals'][category]}")
        
        # Modified education score calculation
        if matched_education:
            education_scores = [profile["education"][edu] for edu in matched_education]
            total_edu_score = sum(education_scores)
            
            if total_edu_score > 18:
                # If total is above 18, only take the highest score
                results["scores"]["education"] = max(education_scores)
            else:
                # If total is 18 or less, take sum of all scores
                results["scores"]["education"] = total_edu_score
        else:
            results["scores"]["education"] = 0
        
        results["totals"]["education"] = 18  # Fixed total score for education
        logger.debug(f"Education score: {results['scores']['education']}/{results['totals']['education']}")
        
        # Suggestions Analysis Debug
        logger.debug("\n[GENERATING SUGGESTIONS]")
        results["suggestions"] = {
            "skills": self.get_skill_suggestions(profile_name, results["matches"]["skills"]),
            "certifications": self.get_certification_suggestions(profile_name, results["matches"]["certifications"])
        }
        
        # Log suggested skills
        logger.debug("Recommended skills to learn:")
        for skill, weight, _ in results["suggestions"]["skills"]:
            logger.debug(f"- {skill} (Priority: {weight}/5)")
            
        # Log suggested certifications
        logger.debug("Recommended certifications:")
        for cert, weight, _ in results["suggestions"]["certifications"]:
            logger.debug(f"- {cert} (Impact: {weight}/5)")
        
        # TODO: REMOVE FOR DEPLOYMENT - Start
        logger.debug("\n[FINAL SCORE CALCULATION]")
        # TODO: REMOVE FOR DEPLOYMENT - End
        
        # Calculate final score with updated weights
        weights = {
            "skills": 50,        # 50% weight for skills
            "certifications": 15, # 15% weight for certifications
            "education": 35      # 35% weight for education
        }
        
        # TODO: REMOVE FOR DEPLOYMENT - Start
        logger.debug("Using weights:")
        for category, weight in weights.items():
            logger.debug(f"{category.title()}: {weight}%")
        # TODO: REMOVE FOR DEPLOYMENT - End
        
        final_score = sum(
            (results["scores"][category] / results["totals"][category]) * weights[category]
            for category in weights.keys()  # Experience removed from scoring
        )
        
        # TODO: REMOVE FOR DEPLOYMENT - Start
        logger.debug("\nCategory-wise scores:")
        for category in weights.keys():
            score = (results["scores"][category] / results["totals"][category]) * weights[category]
            logger.debug(f"{category.title()}: {score:.1f}%")
        logger.debug(f"\nFinal compatibility score: {round(final_score, 1)}%")
        logger.debug("=" * 50)
        # TODO: REMOVE FOR DEPLOYMENT - End
        
        return {
            "score": round(final_score, 1),
            "seniority": seniority,
            "target_level": target_level,
            "exp_years": exp_years,
            "matches": results["matches"],
            "category_scores": results["scores"],
            "category_totals": results["totals"],
            "suggestions": results["suggestions"]
        }

# Initialize Flask app
app = Flask(__name__, 
            template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates')))
app.secret_key = 'your-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

# Initialize the analyzer
analyzer = ResumeAnalyzer()

def get_suggestions(profile, skills_found):
    suggestions = {"skills": [], "certifications": []}
    
    # Get required skills that are missing
    profile_skills = analyzer.job_profile_keywords[profile]["skills"]
    for skill, weight in profile_skills.items():
        if skill not in skills_found:
            resource_links = get_skill_resources(skill) or {"video_course": get_generic_skill_link(skill)}
            suggestions["skills"].append((skill, weight, resource_links))
    
    # Get recommended certifications with links
    profile_certs = analyzer.job_profile_keywords[profile]["certifications"]
    for cert, weight in profile_certs.items():
        resource_links = get_certification_resources(cert) or {"info": get_generic_certification_link(cert)}
        suggestions["certifications"].append((cert, weight, resource_links))
    
    return suggestions

@app.route('/', methods=['GET', 'POST'])
def upload_resume():
    try:
        if request.method == 'POST':
            file = request.files.get('resume')
            profile = request.form.get('job_profile')
            
            # TODO: REMOVE FOR DEPLOYMENT - Start
            logger.debug(f"Processing resume upload for profile: {profile}")
            # TODO: REMOVE FOR DEPLOYMENT - End
            
            if not file or not profile:
                flash("Missing file or profile selection")
                return redirect(request.url)
                
            try:
                ext = file.filename.split('.')[-1].lower()
                # TODO: REMOVE FOR DEPLOYMENT - Start
                logger.debug(f"Processing file with extension: {ext}")
                # TODO: REMOVE FOR DEPLOYMENT - End
                
                text = analyzer.extract_text(BytesIO(file.read()), ext)
                analysis = analyzer.analyze_resume(text, profile)
                
                # Get alternative profiles if score is less than 45%
                alternative_profiles = {}
                if analysis["score"] < 45:
                    # TODO: REMOVE FOR DEPLOYMENT - Start
                    logger.debug("Score below 45%, checking alternative profiles")
                    # TODO: REMOVE FOR DEPLOYMENT - End
                    
                    all_profiles = analyzer.analyze_all_profiles(text)
                    all_profiles.pop(profile, None)
                    alternative_profiles = dict(list(all_profiles.items())[:3])
                    
                    # TODO: REMOVE FOR DEPLOYMENT - Start
                    logger.debug(f"Found alternative profiles: {alternative_profiles}")
                    # TODO: REMOVE FOR DEPLOYMENT - End
                
                suggestions = get_suggestions(profile, analysis["matches"]["skills"])
                
                return render_template('result.html', 
                                    result=analysis, 
                                    profile=profile,
                                    job_profile_keywords=analyzer.job_profile_keywords,
                                    alternative_profiles=alternative_profiles,
                                    suggestions=suggestions,
                                    show_missing_experience=False)
            except Exception as e:
                # TODO: REMOVE FOR DEPLOYMENT - Start
                logger.error(f"Error processing file: {str(e)}", exc_info=True)
                # TODO: REMOVE FOR DEPLOYMENT - End
                flash(str(e))
                return redirect(request.url)
        
        # TODO: REMOVE FOR DEPLOYMENT - Start
        logger.debug("Rendering upload template with profiles: %s", list(analyzer.job_profile_keywords.keys()))
        # TODO: REMOVE FOR DEPLOYMENT - End
        return render_template('upload.html', profiles=analyzer.job_profile_keywords.keys())
    except Exception as e:
        # TODO: REMOVE FOR DEPLOYMENT - Start
        logger.error(f"Unexpected error in upload_resume: {str(e)}", exc_info=True)
        # TODO: REMOVE FOR DEPLOYMENT - End
        flash("An unexpected error occurred")
        return render_template('upload.html', profiles=[])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)
