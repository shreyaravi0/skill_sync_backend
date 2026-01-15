# app/ml/ats_scorer.py
import re
from typing import Dict, List, Tuple
import PyPDF2
import docx
from io import BytesIO

class ATSScorer:
    """
    ATS (Applicant Tracking System) Resume Scorer
    Analyzes resumes and provides scores with improvement suggestions
    """
    
    def __init__(self):
        # Common ATS keywords by category
        self.keyword_categories = {
            'technical_skills': [
                'python', 'java', 'javascript', 'react', 'node.js', 'sql', 'aws',
                'docker', 'kubernetes', 'git', 'agile', 'machine learning', 'ai',
                'data analysis', 'api', 'rest', 'microservices', 'cloud', 'devops',
                'typescript', 'mongodb', 'postgresql', 'redis', 'django', 'flask',
                'fastapi', 'spring', 'angular', 'vue', 'html', 'css', 'bootstrap',
                'tailwind', 'graphql', 'ci/cd', 'jenkins', 'terraform', 'ansible'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'critical thinking', 'time management', 'collaboration',
                'adaptability', 'creativity', 'presentation', 'negotiation',
                'conflict resolution', 'decision making', 'strategic thinking',
                'emotional intelligence', 'mentoring', 'coaching', 'public speaking'
            ],
            'action_verbs': [
                'developed', 'created', 'managed', 'led', 'improved', 'increased',
                'reduced', 'achieved', 'implemented', 'designed', 'optimized',
                'launched', 'delivered', 'coordinated', 'analyzed', 'built',
                'established', 'streamlined', 'pioneered', 'spearheaded', 'executed',
                'transformed', 'accelerated', 'expanded', 'strengthened', 'orchestrated'
            ],
            'education': [
                'bachelor', 'master', 'phd', 'degree', 'university', 'college',
                'certification', 'certified', 'diploma', 'graduate', 'mba',
                'associate', 'doctorate', 'academic', 'coursework', 'gpa'
            ]
        }
        
        # Section headers to look for
        self.section_headers = [
            'experience', 'education', 'skills', 'projects', 'certifications',
            'summary', 'objective', 'achievements', 'work history', 'employment',
            'professional experience', 'technical skills', 'work experience'
        ]
    
    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            docx_file = BytesIO(file_bytes)
            doc = docx.Document(docx_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise Exception(f"Failed to extract text from DOCX: {str(e)}")
    
    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Extract text based on file type"""
        if filename.lower().endswith('.pdf'):
            return self.extract_text_from_pdf(file_bytes)
        elif filename.lower().endswith('.docx'):
            return self.extract_text_from_docx(file_bytes)
        else:
            raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")
    
    def calculate_keyword_score(self, text: str) -> Tuple[int, Dict, List]:
        """Calculate keyword presence score"""
        text_lower = text.lower()
        matched_keywords = {category: [] for category in self.keyword_categories}
        total_possible = sum(len(keywords) for keywords in self.keyword_categories.values())
        total_matched = 0
        
        for category, keywords in self.keyword_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matched_keywords[category].append(keyword)
                    total_matched += 1
        
        # Calculate missing important keywords
        missing_keywords = []
        for category, keywords in self.keyword_categories.items():
            if category in ['technical_skills', 'action_verbs']:
                missing = [kw for kw in keywords if kw not in text_lower]
                missing_keywords.extend(missing[:5])  # Top 5 missing per category
        
        score = min(100, int((total_matched / total_possible) * 150))  # Scale to 100
        return score, matched_keywords, missing_keywords
    
    def calculate_formatting_score(self, text: str) -> Tuple[int, List]:
        """Calculate formatting and structure score"""
        score = 0
        suggestions = []
        
        # Check for sections
        found_sections = []
        for header in self.section_headers:
            if re.search(rf'\b{header}\b', text, re.IGNORECASE):
                found_sections.append(header)
                score += 10
        
        if len(found_sections) < 3:
            suggestions.append("Add clear section headers (Experience, Education, Skills, etc.)")
        
        # Check for bullet points
        bullet_count = text.count('•') + text.count('●') + text.count('-')
        if bullet_count > 5:
            score += 20
        else:
            suggestions.append("Use bullet points to organize information clearly")
        
        # Check for contact information
        has_email = bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
        has_phone = bool(re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text))
        
        if has_email:
            score += 15
        else:
            suggestions.append("Include a professional email address")
        
        if has_phone:
            score += 15
        else:
            suggestions.append("Include a phone number")
        
        # Check length (ideal: 400-1000 words)
        word_count = len(text.split())
        if 400 <= word_count <= 1000:
            score += 20
        elif word_count < 400:
            suggestions.append("Resume seems too short. Add more details about your experience")
        else:
            suggestions.append("Resume is too long. Keep it concise (1-2 pages)")
        
        # Check for URLs (LinkedIn, GitHub, etc.)
        if re.search(r'https?://', text):
            score += 10
        else:
            suggestions.append("Add links to LinkedIn, GitHub, or portfolio")
        
        return min(100, score), suggestions
    
    def calculate_readability_score(self, text: str) -> Tuple[int, List]:
        """Calculate readability score"""
        score = 0
        suggestions = []
        
        sentences = text.split('.')
        words = text.split()
        
        if len(sentences) == 0 or len(words) == 0:
            return 0, ["Resume appears to be empty or poorly formatted"]
        
        # Average sentence length (ideal: 15-20 words)
        avg_sentence_length = len(words) / max(len(sentences), 1)
        if 10 <= avg_sentence_length <= 25:
            score += 30
        elif avg_sentence_length > 25:
            suggestions.append("Use shorter sentences for better readability")
        
        # Check for passive voice indicators
        passive_indicators = ['was', 'were', 'been', 'being', 'is', 'are']
        passive_count = sum(text.lower().count(word) for word in passive_indicators)
        if passive_count < len(words) * 0.05:  # Less than 5%
            score += 25
        else:
            suggestions.append("Use active voice instead of passive (e.g., 'Led team' vs 'Team was led by me')")
        
        # Check for action verbs
        action_verb_count = sum(1 for verb in self.keyword_categories['action_verbs'] 
                                if verb in text.lower())
        if action_verb_count >= 5:
            score += 25
        else:
            suggestions.append("Start bullet points with strong action verbs")
        
        # Check for numbers/metrics
        number_count = len(re.findall(r'\d+', text))
        if number_count >= 3:
            score += 20
        else:
            suggestions.append("Include quantifiable achievements (e.g., 'Increased sales by 30%')")
        
        return min(100, score), suggestions
    
    def calculate_completeness_score(self, text: str) -> Tuple[int, List]:
        """Check if resume has all essential sections"""
        score = 0
        suggestions = []
        text_lower = text.lower()
        
        # Essential sections
        essential_sections = {
            'experience': ['experience', 'work history', 'employment', 'professional experience'],
            'education': ['education', 'academic', 'degree'],
            'skills': ['skills', 'technical skills', 'competencies'],
            'contact': ['email', 'phone', '@', 'linkedin']
        }
        
        for section, keywords in essential_sections.items():
            if any(keyword in text_lower for keyword in keywords):
                score += 25
            else:
                suggestions.append(f"Add a '{section.title()}' section")
        
        return score, suggestions
    
    def generate_overall_feedback(self, overall_score: int) -> str:
        """Generate overall feedback based on score"""
        if overall_score >= 90:
            return "Excellent! Your resume is highly optimized for ATS systems."
        elif overall_score >= 75:
            return "Good resume! A few minor improvements will make it ATS-perfect."
        elif overall_score >= 60:
            return "Your resume needs some optimization to pass ATS filters effectively."
        elif overall_score >= 40:
            return "Significant improvements needed. Focus on keywords and structure."
        else:
            return "Major revisions required. Consider restructuring your entire resume."
    
    def score_resume(self, file_bytes: bytes, filename: str) -> Dict:
        """
        Main scoring function
        Returns comprehensive analysis with scores and suggestions
        """
        # Extract text
        text = self.extract_text(file_bytes, filename)
        
        if not text.strip():
            raise ValueError("Unable to extract text from resume. File may be corrupted or empty.")
        
        # Calculate individual scores
        keyword_score, matched_keywords, missing_keywords = self.calculate_keyword_score(text)
        formatting_score, formatting_suggestions = self.calculate_formatting_score(text)
        readability_score, readability_suggestions = self.calculate_readability_score(text)
        completeness_score, completeness_suggestions = self.calculate_completeness_score(text)
        
        # Calculate overall score (weighted average)
        overall_score = int(
            keyword_score * 0.35 +
            formatting_score * 0.25 +
            readability_score * 0.25 +
            completeness_score * 0.15
        )
        
        # Combine all suggestions
        all_suggestions = (
            formatting_suggestions +
            readability_suggestions +
            completeness_suggestions
        )
        
        # Add keyword-specific suggestions
        if missing_keywords:
            all_suggestions.insert(0, 
                f"Consider adding these keywords: {', '.join(missing_keywords[:10])}")
        
        # Word count
        word_count = len(text.split())
        
        return {
            'overall_score': overall_score,
            'keyword_score': keyword_score,
            'formatting_score': formatting_score,
            'readability_score': readability_score,
            'completeness_score': completeness_score,
            'matched_keywords': matched_keywords,
            'missing_keywords': missing_keywords[:15],  # Top 15
            'suggestions': all_suggestions,
            'overall_feedback': self.generate_overall_feedback(overall_score),
            'word_count': word_count,
            'resume_text_preview': text[:500] + '...' if len(text) > 500 else text
        }