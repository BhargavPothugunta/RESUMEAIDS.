from flask import Flask, request, render_template, jsonify
import os
import re
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_name(text):
    # Common name patterns
    name_patterns = [
        name:
    ]
    
    for pattern in name_patterns:
        matches = re.search(pattern, text)
        if matches:
            name = matches.group(1).strip()
            # Validate name (basic check)
            if len(name.split()) >= 2 and len(name) <= 50:
                return name
    return None

def extract_email(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else None

def extract_phone(text):
    phone_patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Standard US format
        r'\b\+\d{1,3}[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,4}\b',  # International format
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}'  # (123) 456-7890 format
    ]
    
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            return phones[0]
    return None

def extract_skills(text):
    # Expanded skill keywords
    technical_skills = [
        'python', 'java', 'javascript', 'typescript', 'html', 'css', 'react', 'angular',
        'vue', 'node', 'express', 'django', 'flask', 'sql', 'mysql', 'postgresql',
        'mongodb', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
        'machine learning', 'ai', 'data science', 'tensorflow', 'pytorch', 'nlp',
        'devops', 'ci/cd', 'agile', 'scrum', 'rest api', 'graphql'
    ]
    
    soft_skills = [
        'leadership', 'communication', 'teamwork', 'problem solving',
        'project management', 'time management', 'analytical', 'creative',
        'collaboration', 'adaptability', 'organization'
    ]
    
    found_skills = {
        'technical': [],
        'soft': []
    }
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    for skill in technical_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills['technical'].append(skill)
            
    for skill in soft_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills['soft'].append(skill)
            
    return found_skills

def extract_experience(text):
    experiences = []
    
    # Common date patterns
    date_patterns = [
        r'(?i)(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s.-]+\d{4}',
        r'\d{2}/\d{4}',
        r'\d{4}'
    ]
    
    # Split text into potential experience sections
    sections = re.split(r'\n\n+', text)
    
    for section in sections:
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, section, re.IGNORECASE))
        
        if len(dates) >= 1:
            # Clean up the section text
            clean_text = ' '.join(section.split())
            if len(clean_text) > 30:  # Minimum length to be considered valid
                experiences.append({
                    'dates': dates,
                    'description': clean_text[:500]  # Limit description length
                })
    
    return experiences[:5]  # Return up to 5 most recent experiences

def extract_achievements(text):
    achievements = []
    
    # Achievement indicators
    achievement_patterns = [
        r'(?i)(?:achievement|accomplishment|award|honor|recognition)s?[:\s]+(.*?)(?:\n|$)',
        r'(?i)(?:^|\n)[\s•-]*(?:won|achieved|earned|received|awarded)+(.*?)(?:\n|$)',
        r'(?i)(?:^|\n)[\s•-]*(?:led|managed|developed|created|implemented)+(.*?)(?:\n|$)'
    ]
    
    for pattern in achievement_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            achievement = match.group(1).strip()
            if len(achievement) > 10:  # Minimum length to be considered valid
                achievements.append(achievement)
    
    # Also look for bullet points that might indicate achievements
    bullet_achievements = re.findall(r'(?:^|\n)\s*[•\-]\s*(.*?)(?:\n|$)', text)
    for achievement in bullet_achievements:
        if any(word in achievement.lower() for word in ['increased', 'decreased', 'improved', 'reduced', 'achieved', 'won']):
            if len(achievement) > 10:
                achievements.append(achievement)
    
    return list(set(achievements))[:5]  # Return up to 5 unique achievements

def parse_resume(file_content):
    # Convert bytes to string for demo
    text = file_content.decode('utf-8', errors='ignore')
    
    # Extract information
    parsed_data = {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'skills': extract_skills(text),
        'experience': extract_experience(text),
        'achievements': extract_achievements(text),
        'raw_text': text[:500] + '...' if len(text) > 500 else text
    }
    
    return parsed_data

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/parse', methods=['POST'])
def parse():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith(('.txt', '.pdf')):
        return jsonify({'error': 'Only PDF and TXT files are supported'}), 400
    
    try:
        file_content = file.read()
        result = parse_resume(file_content)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=3000)