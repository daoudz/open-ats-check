"""
job_matcher.py - Compare a CV/resume against a job description.
Identifies matching qualifications (pros), gaps (cons), and actionable recommendations.
"""

import re
from collections import Counter


def compare_cv_to_job(cv_text, job_text):
    """
    Compare CV text against a job description.
    
    Returns:
        dict with:
            - match_score: overall match percentage (0-100)
            - pros: list of matching qualifications
            - cons: list of gaps/missing qualifications
            - recommendations: actionable suggestions
            - keyword_analysis: detailed keyword comparison
    """
    cv_lower = cv_text.lower()
    job_lower = job_text.lower()

    # Extract key terms from job description
    job_skills = _extract_skills_from_text(job_lower)
    cv_skills = _extract_skills_from_text(cv_lower)

    job_requirements = _extract_requirements(job_lower)
    job_keywords = _extract_important_keywords(job_lower)
    cv_keywords = _extract_important_keywords(cv_lower)

    # ── Matching analysis ──
    matched_skills = job_skills & cv_skills
    missing_skills = job_skills - cv_skills
    extra_skills = cv_skills - job_skills

    matched_keywords = job_keywords & cv_keywords
    missing_keywords = job_keywords - cv_keywords

    # ── Score calculation ──
    if len(job_skills) > 0:
        skill_match_pct = len(matched_skills) / len(job_skills) * 100
    else:
        skill_match_pct = 50  # neutral if no skills extracted from JD

    if len(job_keywords) > 0:
        keyword_match_pct = len(matched_keywords) / len(job_keywords) * 100
    else:
        keyword_match_pct = 50

    # Weighted score
    match_score = skill_match_pct * 0.6 + keyword_match_pct * 0.4

    # ── Build pros ──
    pros = []
    if matched_skills:
        pros.append(f"Your CV matches {len(matched_skills)} required skill(s): {', '.join(sorted(matched_skills)[:12])}")
    if matched_keywords:
        pros.append(f"{len(matched_keywords)} job keyword(s) found in your CV")

    # Check for experience level match
    job_years = _extract_years_requirement(job_lower)
    cv_years = _estimate_cv_years(cv_lower)
    if job_years and cv_years:
        if cv_years >= job_years:
            pros.append(f"Your experience (~{cv_years} years) meets the {job_years}+ year requirement")
        else:
            pass  # handled in cons

    # Check for degree match
    job_degree = _extract_degree_requirement(job_lower)
    cv_degree = _get_cv_degree_level(cv_lower)
    if job_degree and cv_degree >= job_degree:
        degree_names = {1: 'Diploma', 2: 'Associate', 3: "Bachelor's", 4: "Master's", 5: 'Doctorate'}
        pros.append(f"Your education level ({degree_names.get(cv_degree, 'Unknown')}) meets the requirement")

    if extra_skills:
        pros.append(f"Additional skills you bring: {', '.join(sorted(extra_skills)[:8])}")

    # ── Build cons ──
    cons = []
    if missing_skills:
        cons.append(f"Missing {len(missing_skills)} required skill(s): {', '.join(sorted(missing_skills)[:12])}")
    if missing_keywords:
        top_missing = sorted(missing_keywords)[:8]
        cons.append(f"Missing key terms from job description: {', '.join(top_missing)}")

    if job_years and cv_years and cv_years < job_years:
        cons.append(f"Experience gap: job requires {job_years}+ years, your CV shows ~{cv_years} years")

    if job_degree and cv_degree < job_degree:
        degree_names = {1: 'Diploma', 2: 'Associate', 3: "Bachelor's", 4: "Master's", 5: 'Doctorate'}
        cons.append(f"Education gap: job requires {degree_names.get(job_degree, 'higher degree')}, your CV shows {degree_names.get(cv_degree, 'lower level')}")

    # ── Recommendations ──
    recommendations = []
    if missing_skills:
        recommendations.append({
            'action': 'add',
            'priority': 'high',
            'text': f"Add these skills to your CV if you have them: {', '.join(sorted(missing_skills)[:10])}",
        })
    if missing_keywords:
        recommendations.append({
            'action': 'add',
            'priority': 'medium',
            'text': f"Incorporate these keywords naturally into your CV: {', '.join(sorted(missing_keywords)[:8])}",
        })
    if extra_skills and len(extra_skills) > 10:
        recommendations.append({
            'action': 'remove',
            'priority': 'low',
            'text': "Consider removing irrelevant skills to keep your CV focused on this role.",
        })
    if not pros:
        recommendations.append({
            'action': 'enhance',
            'priority': 'high',
            'text': "Your CV has very low overlap with this job description. Consider tailoring it specifically for this role.",
        })

    # Check for specific action items
    if 'cover letter' in job_lower or 'letter of interest' in job_lower:
        recommendations.append({
            'action': 'enhance',
            'priority': 'medium',
            'text': "The job listing mentions a cover letter — make sure to prepare one.",
        })

    # Always recommend tailoring
    recommendations.append({
        'action': 'enhance',
        'priority': 'medium',
        'text': f"Mirror the job description's language. Use their exact terms where possible.",
    })

    return {
        'match_score': round(match_score, 1),
        'pros': pros,
        'cons': cons,
        'recommendations': recommendations,
        'keyword_analysis': {
            'job_skills': sorted(job_skills),
            'cv_skills': sorted(cv_skills),
            'matched_skills': sorted(matched_skills),
            'missing_skills': sorted(missing_skills),
            'extra_skills': sorted(extra_skills),
            'job_keywords_count': len(job_keywords),
            'matched_keywords_count': len(matched_keywords),
        }
    }


# ──────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────

SKILL_DB = {
    # Tech
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
    'swift', 'kotlin', 'php', 'scala', 'r', 'sql', 'nosql', 'graphql',
    'html', 'css', 'react', 'angular', 'vue', 'node.js', 'next.js',
    'django', 'flask', 'spring', 'express', 'laravel', 'rails',
    'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins',
    'aws', 'azure', 'gcp', 'google cloud', 'heroku',
    'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
    'git', 'linux', 'bash', 'rest api', 'microservices',
    'machine learning', 'deep learning', 'nlp', 'tensorflow', 'pytorch',
    'pandas', 'numpy', 'spark', 'hadoop', 'scikit-learn',
    # Design
    'figma', 'sketch', 'photoshop', 'illustrator', 'adobe suite',
    # Business
    'excel', 'power bi', 'tableau', 'salesforce', 'sap', 'oracle',
    'google analytics', 'data analysis', 'business intelligence',
    # Methodologies
    'agile', 'scrum', 'kanban', 'six sigma', 'lean', 'devops', 'ci/cd',
    # Marketing
    'seo', 'sem', 'ppc', 'google ads', 'content marketing', 'email marketing',
    # PM
    'jira', 'confluence', 'trello', 'asana', 'project management', 'product management',
    # UX
    'ux design', 'ui design', 'wireframing', 'prototyping', 'user research',
    # Soft
    'communication', 'leadership', 'teamwork', 'problem solving',
    'critical thinking', 'time management', 'collaboration', 'negotiation',
}


def _extract_skills_from_text(text):
    """Extract known skills mentioned in text."""
    found = set()
    for skill in SKILL_DB:
        if skill in text:
            found.add(skill)
    return found


def _extract_important_keywords(text):
    """Extract important multi-word and single-word keywords from text."""
    # Remove common stop words and extract meaningful terms
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'shall', 'can', 'need', 'must',
        'this', 'that', 'these', 'those', 'it', 'its', 'we', 'our', 'you',
        'your', 'they', 'their', 'he', 'she', 'him', 'her', 'who', 'which',
        'what', 'when', 'where', 'how', 'why', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'not', 'only',
        'same', 'so', 'than', 'too', 'very', 'just', 'about', 'above', 'also',
        'as', 'if', 'then', 'up', 'out', 'into', 'over', 'after', 'before',
        'between', 'under', 'again', 'further', 'once', 'here', 'there',
        'any', 'able', 'work', 'working', 'experience', 'including',
        'within', 'across', 'well', 'role', 'position', 'candidate',
        'required', 'preferred', 'minimum', 'strong', 'excellent',
        'ability', 'skills', 'knowledge', 'requirements', 'qualifications',
        'responsibilities', 'duties', 'looking', 'seeking', 'join',
    }
    
    words = re.findall(r'\b[a-z]{3,}\b', text)
    keywords = set()
    for word in words:
        if word not in stop_words and len(word) > 3:
            keywords.add(word)

    # Only keep words that appear meaningfully (not extremely common)
    word_counts = Counter(words)
    significant = {w for w, c in word_counts.items() if 1 <= c <= 20 and w not in stop_words and len(w) > 3}
    
    return significant


def _extract_requirements(text):
    """Extract specific requirements from a job description."""
    requirements = []
    
    # Look for lines after "requirements", "qualifications", etc.
    req_patterns = [
        r'(?:requirements?|qualifications?|must have|required|what you.?ll need)[\s:]*\n((?:.*\n)*?)\n\n',
    ]
    for pattern in req_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            lines = [l.strip().lstrip('•-*▪ ') for l in m.split('\n') if l.strip()]
            requirements.extend(lines)
    
    return requirements


def _extract_years_requirement(text):
    """Extract years-of-experience requirement from job description."""
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|exp)',
        r'(?:minimum|at least|min)\s*(\d+)\s*years?',
        r'(\d+)\+?\s*years?\s*(?:in|of|with)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def _estimate_cv_years(text):
    """Estimate years of experience from CV."""
    years = re.findall(r'\b((?:19|20)\d{2})\b', text)
    if len(years) >= 2:
        years_int = [int(y) for y in years]
        return max(years_int) - min(years_int)
    return None


def _extract_degree_requirement(text):
    """Extract minimum degree requirement from job description."""
    degree_map = {
        'phd': 5, 'ph.d': 5, 'doctorate': 5, 'doctoral': 5,
        'master': 4, 'masters': 4, "master's": 4, 'mba': 4,
        'bachelor': 3, 'bachelors': 3, "bachelor's": 3,
        'associate': 2,
        'diploma': 1,
    }
    for keyword, level in sorted(degree_map.items(), key=lambda x: -x[1]):
        if keyword in text:
            return level
    return None


def _get_cv_degree_level(text):
    """Get highest degree level from CV."""
    degree_map = {
        'phd': 5, 'ph.d': 5, 'doctorate': 5,
        'master': 4, 'masters': 4, "master's": 4, 'mba': 4, 'msc': 4,
        'bachelor': 3, 'bachelors': 3, "bachelor's": 3, 'bsc': 3, 'b.s': 3,
        'associate': 2,
        'diploma': 1, 'certificate': 1,
    }
    max_level = 0
    for keyword, level in degree_map.items():
        if keyword in text:
            max_level = max(max_level, level)
    return max_level
