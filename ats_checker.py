"""
ats_checker.py - ATS (Applicant Tracking System) analysis engine.
Provides 6 scoring modules that evaluate a resume against ATS standards.
"""

import re
from collections import Counter


# ──────────────────────────────────────────────
# Skill / keyword databases
# ──────────────────────────────────────────────

HARD_SKILLS = {
    # Programming & Development
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
    'swift', 'kotlin', 'php', 'scala', 'r', 'matlab', 'sql', 'nosql', 'graphql',
    'html', 'css', 'sass', 'less', 'react', 'angular', 'vue', 'svelte', 'next.js',
    'node.js', 'express', 'django', 'flask', 'spring', 'laravel', 'rails',
    'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'github actions',
    'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'vercel',
    'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'dynamodb',
    'git', 'linux', 'bash', 'powershell', 'rest api', 'microservices',
    'machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow',
    'pytorch', 'scikit-learn', 'pandas', 'numpy', 'spark', 'hadoop',
    # Design & Creative
    'figma', 'sketch', 'adobe suite', 'photoshop', 'illustrator', 'indesign',
    'after effects', 'premiere pro', 'blender', 'autocad', 'solidworks',
    # Business & Analytics
    'excel', 'power bi', 'tableau', 'salesforce', 'hubspot', 'sap', 'oracle',
    'google analytics', 'data analysis', 'data visualization', 'business intelligence',
    'financial modeling', 'forecasting', 'budgeting',
    # Methodologies
    'agile', 'scrum', 'kanban', 'waterfall', 'six sigma', 'lean', 'devops',
    'ci/cd', 'tdd', 'bdd', 'oop', 'functional programming',
    # Marketing & Digital
    'seo', 'sem', 'ppc', 'google ads', 'facebook ads', 'content marketing',
    'email marketing', 'social media marketing', 'copywriting', 'a/b testing',
    # Other
    'jira', 'confluence', 'trello', 'asana', 'slack', 'microsoft office',
    'project management', 'product management', 'ux design', 'ui design',
    'user research', 'wireframing', 'prototyping', 'usability testing',
    'blockchain', 'cybersecurity', 'networking', 'cloud computing',
}

SOFT_SKILLS = {
    'communication', 'leadership', 'teamwork', 'problem solving', 'problem-solving',
    'critical thinking', 'time management', 'adaptability', 'creativity',
    'collaboration', 'negotiation', 'conflict resolution', 'decision making',
    'decision-making', 'attention to detail', 'strategic thinking', 'mentoring',
    'coaching', 'presentation', 'public speaking', 'writing', 'interpersonal',
    'organizational', 'multitasking', 'self-motivated', 'initiative',
    'analytical', 'research', 'planning', 'customer service', 'empathy',
    'emotional intelligence', 'flexibility', 'resilience', 'accountability',
    'work ethic', 'verbal communication', 'written communication',
}

STANDARD_SECTIONS = {
    'work experience', 'experience', 'professional experience', 'employment history',
    'employment', 'career history',
    'education', 'academic background', 'academic', 'qualifications',
    'skills', 'technical skills', 'core competencies', 'competencies', 'key skills',
    'certifications', 'certificates', 'licenses', 'credentials',
    'summary', 'professional summary', 'objective', 'career objective', 'profile',
    'about me', 'overview',
    'projects', 'portfolio', 'key projects',
    'awards', 'honors', 'achievements', 'accomplishments',
    'references',
    'volunteer', 'volunteering', 'volunteer experience',
    'languages',
    'publications',
    'contact', 'contact information', 'personal information', 'personal details',
}

DEGREE_LEVELS = {
    'phd': 5, 'ph.d': 5, 'doctorate': 5, 'doctoral': 5,
    'master': 4, 'masters': 4, "master's": 4, 'mba': 4, 'msc': 4, 'ma': 4, 'ms': 4, 'm.s.': 4,
    'bachelor': 3, 'bachelors': 3, "bachelor's": 3, 'bsc': 3, 'ba': 3, 'bs': 3, 'b.s.': 3, 'b.a.': 3,
    'associate': 2, 'associates': 2, "associate's": 2,
    'diploma': 1, 'certificate': 1, 'certification': 1,
}

CERTIFICATIONS_DB = [
    'pmp', 'capm', 'prince2', 'itil', 'cissp', 'cism', 'cisa',
    'aws certified', 'azure certified', 'google certified',
    'comptia', 'security+', 'network+', 'a+',
    'cpa', 'cfa', 'cfp', 'frm',
    'phr', 'sphr', 'shrm',
    'rn', 'bsn', 'msn',
    'ccna', 'ccnp', 'ccie',
    'scrum master', 'csm', 'safe',
    'six sigma', 'green belt', 'black belt',
    'google analytics certified', 'hubspot certified',
    'salesforce certified', 'tableau certified',
    'pe ', 'p.e.', 'licensed',
]

ACTION_VERBS = [
    'achieved', 'accelerated', 'accomplished', 'administered', 'advanced',
    'analyzed', 'architected', 'automated', 'built', 'championed',
    'collaborated', 'consolidated', 'coordinated', 'created', 'decreased',
    'delivered', 'designed', 'developed', 'directed', 'drove',
    'eliminated', 'engineered', 'established', 'exceeded', 'executed',
    'expanded', 'facilitated', 'generated', 'grew', 'headed',
    'implemented', 'improved', 'increased', 'initiated', 'innovated',
    'integrated', 'launched', 'led', 'managed', 'mentored',
    'modernized', 'negotiated', 'optimized', 'orchestrated', 'organized',
    'overhauled', 'oversaw', 'partnered', 'pioneered', 'planned',
    'produced', 'propelled', 'reduced', 're-engineered', 'resolved',
    'restructured', 'revamped', 'scaled', 'secured', 'simplified',
    'spearheaded', 'streamlined', 'strengthened', 'supervised', 'surpassed',
    'trained', 'transformed', 'upgraded',
]


# ──────────────────────────────────────────────
# Main analysis function
# ──────────────────────────────────────────────

def analyze_resume(text, metadata=None):
    """
    Run all 6 ATS analysis modules on the resume text.
    
    Returns:
        dict with:
            - overall_score: weighted average (0-100)
            - sections: list of per-module results
    """
    if metadata is None:
        metadata = {}

    sections = [
        _analyze_keywords(text),
        _analyze_formatting(text, metadata),
        _analyze_contact_info(text),
        _analyze_experience(text),
        _analyze_education(text),
        _analyze_semantic(text),
    ]

    # Weighted average: keywords and experience weigh more
    weights = [25, 15, 15, 20, 15, 10]
    total_weight = sum(weights)
    overall = sum(s['score'] * w for s, w in zip(sections, weights)) / total_weight

    return {
        'overall_score': round(overall, 1),
        'sections': sections,
    }


# ──────────────────────────────────────────────
# 1. Keyword Matching
# ──────────────────────────────────────────────

def _analyze_keywords(text):
    text_lower = text.lower()
    
    found_hard = [s for s in HARD_SKILLS if s in text_lower]
    found_soft = [s for s in SOFT_SKILLS if s in text_lower]
    
    # Score based on number of skills found
    hard_score = min(len(found_hard) / 8 * 100, 100)  # 8+ hard skills = 100
    soft_score = min(len(found_soft) / 4 * 100, 100)   # 4+ soft skills = 100
    
    # Hard skills weigh 70%, soft 30%
    score = hard_score * 0.7 + soft_score * 0.3

    findings = []
    if found_hard:
        findings.append(f"Found {len(found_hard)} hard skill(s): {', '.join(sorted(found_hard)[:15])}")
    else:
        findings.append("No recognizable hard skills found. Add specific tools, technologies, and methodologies.")
    
    if found_soft:
        findings.append(f"Found {len(found_soft)} soft skill(s): {', '.join(sorted(found_soft)[:10])}")
    else:
        findings.append("No soft skills detected. Consider adding communication, leadership, or teamwork keywords.")

    recommendations = []
    if len(found_hard) < 5:
        recommendations.append("Add more specific technical skills and tools relevant to your target role.")
    if len(found_soft) < 3:
        recommendations.append("Include soft skills like 'collaboration', 'problem-solving', or 'leadership'.")

    return {
        'name': 'Keyword Matching',
        'score': round(score, 1),
        'icon': '🔑',
        'findings': findings,
        'recommendations': recommendations,
        'details': {
            'hard_skills': sorted(found_hard),
            'soft_skills': sorted(found_soft),
            'hard_count': len(found_hard),
            'soft_count': len(found_soft),
        }
    }


# ──────────────────────────────────────────────
# 2. Formatting & Parseability
# ──────────────────────────────────────────────

def _analyze_formatting(text, metadata):
    score = 100
    findings = []
    recommendations = []

    # Check for standard section headings
    lines = text.split('\n')
    found_sections = []
    for line in lines:
        stripped = line.strip().lower().rstrip(':')
        if stripped in STANDARD_SECTIONS:
            found_sections.append(stripped)

    essential_sections = ['experience', 'work experience', 'professional experience', 'employment history', 'employment']
    has_experience = any(s in found_sections for s in essential_sections)
    
    education_sections = ['education', 'academic background', 'qualifications']
    has_education = any(s in found_sections for s in education_sections)
    
    skills_sections = ['skills', 'technical skills', 'core competencies', 'competencies', 'key skills']
    has_skills = any(s in found_sections for s in skills_sections)

    if has_experience:
        findings.append("✅ Work Experience section found")
    else:
        findings.append("❌ No standard 'Work Experience' heading detected")
        recommendations.append("Add a clear 'Work Experience' or 'Professional Experience' section heading.")
        score -= 25

    if has_education:
        findings.append("✅ Education section found")
    else:
        findings.append("❌ No standard 'Education' heading detected")
        recommendations.append("Add a clear 'Education' section heading.")
        score -= 20

    if has_skills:
        findings.append("✅ Skills section found")
    else:
        findings.append("❌ No standard 'Skills' heading detected")
        recommendations.append("Add a dedicated 'Skills' or 'Technical Skills' section.")
        score -= 15

    # Check for overly short resume
    word_count = len(text.split())
    if word_count < 100:
        findings.append(f"⚠️ Resume is very short ({word_count} words)")
        recommendations.append("Your resume seems too brief. Aim for at least 300-600 words.")
        score -= 20
    elif word_count < 300:
        findings.append(f"⚠️ Resume is somewhat short ({word_count} words)")
        recommendations.append("Consider adding more detail to your experience and skills.")
        score -= 10
    else:
        findings.append(f"✅ Good length ({word_count} words)")

    # Check for special characters that may confuse parsers
    special_chars = len(re.findall(r'[│┃┆┇┊┋╎╏║╟╢╫╬▶►▸▹◆◇○●■□★☆♦♣♠♥→←↑↓⇒⇐]', text))
    if special_chars > 5:
        findings.append(f"⚠️ Found {special_chars} special/decorative characters")
        recommendations.append("Remove decorative symbols and special characters that may confuse ATS parsers.")
        score -= 10

    # Check for tables (indicated by lots of tab characters)
    tab_count = text.count('\t')
    if tab_count > 20:
        findings.append("⚠️ Possible table-based layout detected (many tab characters)")
        recommendations.append("Avoid table-based layouts. Use a simple, linear format instead.")
        score -= 10

    findings.append(f"Detected {len(found_sections)} standard section heading(s)")

    return {
        'name': 'Formatting & Parseability',
        'score': max(round(score, 1), 0),
        'icon': '📄',
        'findings': findings,
        'recommendations': recommendations,
        'details': {
            'sections_found': found_sections,
            'word_count': word_count,
            'special_chars': special_chars,
        }
    }


# ──────────────────────────────────────────────
# 3. Contact Information Extraction
# ──────────────────────────────────────────────

def _analyze_contact_info(text):
    score = 0
    findings = []
    recommendations = []
    details = {}

    # Email
    email_match = re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        details['email'] = email_match.group()
        findings.append(f"✅ Email found: {email_match.group()}")
        score += 25
    else:
        findings.append("❌ No email address found")
        recommendations.append("Add your professional email address.")

    # Phone
    phone_match = re.search(
        r'(?:\+?\d{1,3}[\s\-.]?)?\(?\d{2,4}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}', text
    )
    if phone_match:
        details['phone'] = phone_match.group().strip()
        findings.append(f"✅ Phone number found: {phone_match.group().strip()}")
        score += 25
    else:
        findings.append("❌ No phone number found")
        recommendations.append("Add your phone number with country code.")

    # LinkedIn
    linkedin_match = re.search(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
    if linkedin_match:
        details['linkedin'] = linkedin_match.group()
        findings.append(f"✅ LinkedIn profile found")
        score += 25
    else:
        findings.append("⚠️ No LinkedIn URL found")
        recommendations.append("Add your LinkedIn profile URL (linkedin.com/in/yourname).")
        score += 5  # Not critical

    # Name detection (heuristic: first non-empty line or line with mostly capital words)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if lines:
        first_line = lines[0]
        # Check if it looks like a name (2-4 words, mostly capitalized)
        words = first_line.split()
        if 1 <= len(words) <= 5 and all(w[0].isupper() for w in words if w.isalpha()):
            details['name'] = first_line
            findings.append(f"✅ Name detected: {first_line}")
            score += 15
        else:
            findings.append("⚠️ Could not confidently detect name at the top of resume")
            recommendations.append("Place your full name prominently at the top of your resume.")
            score += 5

    # Location
    location_patterns = [
        r'\b\d{5}(?:-\d{4})?\b',  # ZIP code
        r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, ST
        r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b',  # City, Country
    ]
    for pattern in location_patterns:
        loc_match = re.search(pattern, text)
        if loc_match:
            details['location'] = loc_match.group()
            findings.append(f"✅ Location/address info found")
            score += 10
            break
    else:
        findings.append("⚠️ No location information detected")
        recommendations.append("Add your city and state/country for location-based filtering.")

    return {
        'name': 'Contact Information',
        'score': min(round(score, 1), 100),
        'icon': '📇',
        'findings': findings,
        'recommendations': recommendations,
        'details': details,
    }


# ──────────────────────────────────────────────
# 4. Work Experience & Longevity
# ──────────────────────────────────────────────

def _analyze_experience(text):
    score = 0
    findings = []
    recommendations = []
    details = {}

    # Find date ranges (e.g., "Jan 2020 - Present", "2018 - 2022", "03/2019 – 06/2021")
    date_patterns = [
        r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*\.?\s*\d{4}\s*[-–—to]+\s*(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*\.?\s*\d{4}|[Pp]resent|[Cc]urrent)',
        r'\d{1,2}/\d{4}\s*[-–—to]+\s*(?:\d{1,2}/\d{4}|[Pp]resent|[Cc]urrent)',
        r'\d{4}\s*[-–—to]+\s*(?:\d{4}|[Pp]resent|[Cc]urrent)',
    ]

    all_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        all_dates.extend(matches)

    if all_dates:
        findings.append(f"✅ Found {len(all_dates)} date range(s) in work history")
        score += 30
        details['date_ranges'] = all_dates[:10]
    else:
        findings.append("❌ No date ranges found in work experience")
        recommendations.append("Include clear start and end dates for each role (e.g., 'Jan 2020 - Present').")

    # Calculate approximate years of experience
    years = re.findall(r'\b((?:19|20)\d{2})\b', text)
    if years:
        years_int = [int(y) for y in years]
        min_year = min(years_int)
        max_year = max(years_int)
        exp_years = max_year - min_year
        details['estimated_years'] = exp_years
        if exp_years > 0:
            findings.append(f"📊 Estimated ~{exp_years} year(s) of experience span ({min_year}–{max_year})")
            score += 20
        else:
            findings.append("⚠️ Experience timeline appears very short")
            score += 5

    # Check for employment gaps (simplified heuristic)
    if len(all_dates) >= 2:
        findings.append("✅ Multiple roles detected — good for showing progression")
        score += 15
    elif len(all_dates) == 1:
        findings.append("⚠️ Only one role detected")
        recommendations.append("If you have multiple roles, make sure each has clear date ranges.")
        score += 5

    # Job title detection
    title_keywords = [
        'manager', 'director', 'engineer', 'developer', 'analyst', 'specialist',
        'coordinator', 'consultant', 'administrator', 'architect', 'designer',
        'lead', 'senior', 'junior', 'intern', 'associate', 'vice president', 'vp',
        'chief', 'ceo', 'cto', 'cfo', 'coo', 'president', 'founder', 'co-founder',
        'supervisor', 'technician', 'officer', 'executive', 'head of', 'team lead',
    ]
    text_lower = text.lower()
    found_titles = [t for t in title_keywords if t in text_lower]
    if found_titles:
        findings.append(f"✅ Job title keywords detected: {', '.join(found_titles[:8])}")
        score += 15
        details['title_keywords'] = found_titles
    else:
        findings.append("⚠️ No clear job title keywords detected")
        recommendations.append("Use standard job titles (e.g., 'Software Engineer', 'Marketing Manager').")
        score += 5

    # Check for quantified achievements
    quant_pattern = r'\d+%|\$[\d,]+|\d+\+?\s*(?:year|month|client|customer|user|project|team|member|employee)'
    quantified = re.findall(quant_pattern, text, re.IGNORECASE)
    if quantified:
        findings.append(f"✅ {len(quantified)} quantified achievement(s) found")
        score += 20
        details['quantified'] = quantified[:8]
    else:
        findings.append("⚠️ No quantified achievements found")
        recommendations.append("Add measurable results (e.g., 'increased sales by 30%', 'managed team of 12').")

    return {
        'name': 'Work Experience & Longevity',
        'score': min(round(score, 1), 100),
        'icon': '💼',
        'findings': findings,
        'recommendations': recommendations,
        'details': details,
    }


# ──────────────────────────────────────────────
# 5. Education & Certifications
# ──────────────────────────────────────────────

def _analyze_education(text):
    score = 0
    findings = []
    recommendations = []
    details = {}

    text_lower = text.lower()

    # Degree detection
    found_degrees = []
    max_degree_level = 0
    for keyword, level in DEGREE_LEVELS.items():
        if keyword in text_lower:
            found_degrees.append(keyword)
            max_degree_level = max(max_degree_level, level)

    if found_degrees:
        level_names = {1: 'Diploma/Certificate', 2: 'Associate', 3: 'Bachelor', 4: 'Master', 5: 'Doctorate'}
        findings.append(f"✅ Highest education level detected: {level_names.get(max_degree_level, 'Unknown')}")
        findings.append(f"   Degree keywords found: {', '.join(set(found_degrees))}")
        score += 40
        details['degree_level'] = max_degree_level
        details['degree_keywords'] = list(set(found_degrees))
    else:
        findings.append("⚠️ No degree keywords detected")
        recommendations.append("Include your degree type (e.g., 'Bachelor of Science', 'MBA').")
        details['degree_level'] = 0

    # Certification detection
    found_certs = []
    for cert in CERTIFICATIONS_DB:
        if cert.lower() in text_lower:
            found_certs.append(cert)

    if found_certs:
        findings.append(f"✅ {len(found_certs)} certification(s) detected: {', '.join(found_certs[:8])}")
        score += 35
        details['certifications'] = found_certs
    else:
        findings.append("ℹ️ No specific certifications detected")
        recommendations.append("Add relevant certifications (e.g., PMP, AWS Certified, CPA) if you have them.")
        score += 10  # not always required

    # University / institution name check
    university_keywords = ['university', 'college', 'institute', 'school', 'academy', 'polytechnic']
    has_institution = any(kw in text_lower for kw in university_keywords)
    if has_institution:
        findings.append("✅ Educational institution name found")
        score += 15
    else:
        findings.append("⚠️ No educational institution name detected")
        recommendations.append("Include the name of your university or college.")

    # GPA mention
    gpa_match = re.search(r'(?:gpa|grade|cgpa)[\s:]*(\d\.\d+)', text_lower)
    if gpa_match:
        findings.append(f"ℹ️ GPA mentioned: {gpa_match.group(1)}")
        score += 10
        details['gpa'] = gpa_match.group(1)

    return {
        'name': 'Education & Certifications',
        'score': min(round(score, 1), 100),
        'icon': '🎓',
        'findings': findings,
        'recommendations': recommendations,
        'details': details,
    }


# ──────────────────────────────────────────────
# 6. Semantic / Contextual Analysis
# ──────────────────────────────────────────────

def _analyze_semantic(text):
    score = 0
    findings = []
    recommendations = []
    details = {}

    text_lower = text.lower()
    words = text_lower.split()

    # Action verbs
    found_verbs = [v for v in ACTION_VERBS if v in text_lower]
    if len(found_verbs) >= 8:
        findings.append(f"✅ Strong use of action verbs ({len(found_verbs)} found)")
        score += 30
    elif len(found_verbs) >= 4:
        findings.append(f"✅ Good use of action verbs ({len(found_verbs)} found)")
        score += 20
    elif found_verbs:
        findings.append(f"⚠️ Limited action verb usage ({len(found_verbs)} found)")
        recommendations.append("Use more action verbs like 'achieved', 'implemented', 'led', 'optimized'.")
        score += 10
    else:
        findings.append("❌ No strong action verbs found")
        recommendations.append("Start bullet points with powerful action verbs: 'Developed', 'Managed', 'Increased', etc.")
    details['action_verbs'] = sorted(found_verbs)

    # Quantified results (more thorough check)
    result_patterns = [
        r'(?:increased|decreased|reduced|improved|grew|boosted|cut|saved|generated|delivered|achieved)\s+.*?\d+',
        r'\d+%\s+(?:increase|decrease|improvement|growth|reduction)',
        r'\$[\d,.]+\s*(?:million|billion|k|m|b|revenue|savings|budget)',
        r'\d+\s*(?:clients|customers|users|projects|products|teams)',
    ]
    contextual_results = []
    for pattern in result_patterns:
        matches = re.findall(pattern, text_lower)
        contextual_results.extend(matches)

    if contextual_results:
        findings.append(f"✅ {len(contextual_results)} contextual achievement(s) with metrics found")
        score += 30
        details['contextual_achievements'] = contextual_results[:8]
    else:
        findings.append("⚠️ No contextual achievements with metrics detected")
        recommendations.append("Provide context for your skills: 'Increased sales by 20%' instead of just listing 'Sales'.")

    # First-person pronoun check (ATS best practice: avoid "I", "me", "my")
    pronoun_count = len(re.findall(r'\b(?:I|me|my|myself)\b', text))
    if pronoun_count == 0:
        findings.append("✅ No first-person pronouns (good ATS practice)")
        score += 15
    elif pronoun_count <= 3:
        findings.append(f"⚠️ {pronoun_count} first-person pronoun(s) found")
        recommendations.append("Minimize first-person pronouns (I, me, my). ATS resumes should use implied subject.")
        score += 8
    else:
        findings.append(f"❌ {pronoun_count} first-person pronouns found — too many")
        recommendations.append("Remove first-person pronouns. Instead of 'I managed a team', write 'Managed a team of...'")

    # Buzzword density check
    buzzwords = ['synergy', 'paradigm', 'leverage', 'utilize', 'facilitate', 'ecosystem',
                 'disrupt', 'bandwidth', 'touchpoint', 'circle back', 'deep dive',
                 'move the needle', 'low-hanging fruit', 'best of breed']
    found_buzz = [b for b in buzzwords if b in text_lower]
    if found_buzz:
        findings.append(f"⚠️ {len(found_buzz)} corporate buzzword(s) detected: {', '.join(found_buzz)}")
        recommendations.append("Replace vague buzzwords with specific, measurable language.")
        score += 5
    else:
        findings.append("✅ No excessive corporate buzzwords")
        score += 15

    # Consistency check: bullet points
    bullet_lines = len(re.findall(r'^[\s]*[•\-\*▪▸►]\s', text, re.MULTILINE))
    if bullet_lines >= 5:
        findings.append(f"✅ Good use of bullet points ({bullet_lines} found)")
        score += 10
    elif bullet_lines > 0:
        findings.append(f"ℹ️ Some bullet points found ({bullet_lines})")
        score += 5
    else:
        findings.append("⚠️ No bullet points detected")
        recommendations.append("Use bullet points (• or -) to organize your experience for better readability.")

    return {
        'name': 'Semantic Analysis',
        'score': min(round(score, 1), 100),
        'icon': '🧠',
        'findings': findings,
        'recommendations': recommendations,
        'details': details,
    }
