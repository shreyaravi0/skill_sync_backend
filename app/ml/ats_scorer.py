# app/ml/ats_scorer.py
import re
from typing import Dict, List, Tuple
import PyPDF2
import docx
from io import BytesIO

class ATSScorer:
    """
    ATS (Applicant Tracking System) Resume Scorer
    Focuses on formatting, structure, and essential information presence
    """
    
    def __init__(self):
        # Section headers to look for
        self.section_headers = {
            'experience': ['experience', 'work history', 'employment', 'professional experience', 'work experience'],
            'education': ['education', 'academic', 'degree', 'university', 'college'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'proficiencies'],
            'projects': ['projects', 'portfolio', 'work samples'],
            'certifications': ['certifications', 'certificates', 'licenses'],
            'summary': ['summary', 'objective', 'profile', 'about me']
        }
        
        # Action verbs for experience descriptions
        self.action_verbs = [
            'developed', 'created', 'managed', 'led', 'improved', 'increased',
            'reduced', 'achieved', 'implemented', 'designed', 'optimized',
            'launched', 'delivered', 'coordinated', 'analyzed', 'built',
            'established', 'streamlined', 'pioneered', 'spearheaded', 'executed',
            'transformed', 'accelerated', 'expanded', 'strengthened', 'orchestrated'
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
    
    def calculate_contact_info_score(self, text: str) -> Tuple[int, List, Dict]:
        """Check for essential contact information"""
        score = 0
        suggestions = []
        found_info = {}
        text_lower = text.lower()
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            score += 25
            found_info['email'] = email_match.group()
        else:
            suggestions.append("❌ Missing professional email address")
        
        # Phone number (various formats)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890 or 1234567890
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',     # (123) 456-7890
            r'\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'  # +1-123-456-7890
        ]
        
        phone_found = False
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                score += 25
                found_info['phone'] = phone_match.group()
                phone_found = True
                break
        
        if not phone_found:
            suggestions.append("❌ Missing phone number")
        
        # LinkedIn
        if 'linkedin.com' in text_lower or 'linkedin' in text_lower:
            score += 15
            found_info['linkedin'] = True
        else:
            suggestions.append("💡 Consider adding LinkedIn profile")
        
        # GitHub/Portfolio (optional but good)
        if 'github.com' in text_lower or 'portfolio' in text_lower or re.search(r'https?://', text):
            score += 10
            found_info['portfolio'] = True
        
        # Location (city/state)
        location_indicators = ['city', 'state', ',', 'street', 'address']
        # Simple check: if there's a pattern like "City, State" or just presence of location keywords
        if any(indicator in text_lower for indicator in location_indicators):
            score += 10
            found_info['location'] = True
        
        # Name (check for capitalized words at the beginning)
        lines = text.strip().split('\n')
        if lines and len(lines[0].strip()) > 2:
            score += 15
            found_info['name'] = lines[0].strip()
        else:
            suggestions.append("❌ Add your full name prominently at the top")
        
        return min(100, score), suggestions, found_info
    
    def calculate_structure_score(self, text: str) -> Tuple[int, List, Dict]:
        """Evaluate resume structure and section presence"""
        score = 0
        suggestions = []
        found_sections = {}
        text_lower = text.lower()
        
        # Check for key sections
        for section_name, keywords in self.section_headers.items():
            section_found = False
            for keyword in keywords:
                if re.search(rf'\b{keyword}\b', text_lower):
                    section_found = True
                    found_sections[section_name] = True
                    score += 15
                    break
            
            if not section_found:
                if section_name in ['experience', 'education', 'skills']:
                    suggestions.append(f"❌ Missing critical section: {section_name.title()}")
                else:
                    suggestions.append(f"💡 Consider adding: {section_name.title()} section")
        
        # Bonus for having multiple sections
        if len(found_sections) >= 4:
            score += 10
        
        return min(100, score), suggestions, found_sections
    
    def calculate_formatting_score(self, text: str) -> Tuple[int, List]:
        """Check formatting and readability"""
        score = 0
        suggestions = []
        
        # Check for bullet points (good for ATS and readability)
        bullet_count = text.count('•') + text.count('●') + text.count('○')
        dash_bullets = len(re.findall(r'\n\s*[-–—]\s+', text))
        total_bullets = bullet_count + dash_bullets
        
        if total_bullets >= 10:
            score += 30
        elif total_bullets >= 5:
            score += 20
            suggestions.append("💡 Add more bullet points for better organization")
        else:
            suggestions.append("❌ Use bullet points to list achievements and responsibilities")
        
        # Check length (ideal: 400-1200 words for 1-2 pages)
        word_count = len(text.split())
        
        if 400 <= word_count <= 1200:
            score += 25
        elif word_count < 400:
            score += 10
            suggestions.append("⚠️ Resume seems short. Add more details about your experience")
        elif word_count > 1200:
            score += 15
            suggestions.append("⚠️ Resume is lengthy. Try to keep it concise (1-2 pages)")
        
        # Check for dates (work experience dates)
        date_patterns = [
            r'\b(19|20)\d{2}\b',  # Years like 2020, 2021
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(19|20)\d{2}\b',  # Month Year
            r'\b\d{1,2}/\d{4}\b'  # MM/YYYY
        ]
        
        dates_found = sum(len(re.findall(pattern, text)) for pattern in date_patterns)
        if dates_found >= 2:
            score += 20
        else:
            suggestions.append("💡 Include dates for your work experience and education")
        
        # Check for quantifiable achievements (numbers/percentages)
        numbers = re.findall(r'\d+%|\$\d+|\d+[km]?\+|\d+x', text.lower())
        if len(numbers) >= 3:
            score += 15
        else:
            suggestions.append("💡 Add quantifiable achievements (e.g., 'Increased sales by 30%', 'Managed team of 5')")
        
        # Check for action verbs
        action_verb_count = sum(1 for verb in self.action_verbs if verb in text.lower())
        if action_verb_count >= 5:
            score += 10
        else:
            suggestions.append("💡 Start bullet points with strong action verbs (e.g., 'Led', 'Developed', 'Managed')")
        
        return min(100, score), suggestions
    
    def calculate_readability_score(self, text: str) -> Tuple[int, List]:
        """Assess readability and writing quality"""
        score = 0
        suggestions = []
        
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        words = text.split()
        
        if len(sentences) == 0 or len(words) == 0:
            return 0, ["❌ Resume appears empty or poorly formatted"]
        
        # Average sentence length (shorter is better for resumes)
        avg_sentence_length = len(words) / max(len(sentences), 1)
        
        if 10 <= avg_sentence_length <= 20:
            score += 30
        elif avg_sentence_length > 25:
            score += 10
            suggestions.append("💡 Use shorter, punchier sentences for better readability")
        else:
            score += 20
        
        # Check for passive voice (should be minimal)
        passive_indicators = ['was', 'were', 'been', 'being']
        passive_count = sum(text.lower().count(word) for word in passive_indicators)
        
        if passive_count < len(words) * 0.03:  # Less than 3%
            score += 30
        elif passive_count < len(words) * 0.07:  # Less than 7%
            score += 20
            suggestions.append("💡 Reduce passive voice. Use active voice (e.g., 'Led team' vs 'Team was led by me')")
        else:
            score += 10
            suggestions.append("❌ Too much passive voice. Use active voice for stronger impact")
        
        # Check for proper capitalization (not all caps)
        all_caps_words = len(re.findall(r'\b[A-Z]{4,}\b', text))
        if all_caps_words < 3:
            score += 20
        else:
            suggestions.append("⚠️ Avoid excessive ALL CAPS text")
        
        # Check for spelling/grammar indicators (basic check)
        # Multiple spaces, missing periods, etc.
        if not re.search(r'\s{3,}', text):  # No excessive spacing
            score += 10
        else:
            suggestions.append("💡 Clean up formatting - remove excessive spaces")
        
        # Check for consistent formatting
        if not re.search(r'[a-z]\.[A-Z]', text):  # Basic check for missing spaces after periods
            score += 10
        
        return min(100, score), suggestions
    
    def generate_overall_feedback(self, overall_score: int) -> str:
        """Generate overall feedback based on score"""
        if overall_score >= 90:
            return "🎉 Excellent! Your resume is well-formatted and ATS-friendly."
        elif overall_score >= 75:
            return "✅ Good resume! A few tweaks will make it perfect."
        elif overall_score >= 60:
            return "⚠️ Your resume needs some optimization to pass ATS filters."
        elif overall_score >= 40:
            return "❌ Significant improvements needed. Focus on structure and formatting."
        else:
            return "🔴 Major revisions required. Consider restructuring your resume."
    
    def score_resume(self, file_bytes: bytes, filename: str) -> Dict:
        """
        Main scoring function - focuses on formatting and structure
        Returns comprehensive analysis with scores and suggestions
        """
        # Extract text
        text = self.extract_text(file_bytes, filename)
        
        if not text.strip():
            raise ValueError("Unable to extract text from resume. File may be corrupted or empty.")
        
        # Calculate scores
        contact_score, contact_suggestions, contact_info = self.calculate_contact_info_score(text)
        structure_score, structure_suggestions, found_sections = self.calculate_structure_score(text)
        formatting_score, formatting_suggestions = self.calculate_formatting_score(text)
        readability_score, readability_suggestions = self.calculate_readability_score(text)
        
        # Calculate overall score (weighted average)
        overall_score = int(
            contact_score * 0.30 +      # Contact info is critical
            structure_score * 0.30 +    # Proper sections are essential
            formatting_score * 0.25 +   # Good formatting matters
            readability_score * 0.15    # Readability is important
        )
        
        # Combine all suggestions (prioritize critical issues first)
        all_suggestions = []
        
        # Critical issues first (contact and structure)
        all_suggestions.extend(contact_suggestions)
        all_suggestions.extend(structure_suggestions)
        
        # Then formatting and readability
        all_suggestions.extend(formatting_suggestions)
        all_suggestions.extend(readability_suggestions)
        
        # Word count
        word_count = len(text.split())
        
        return {
            'overall_score': overall_score,
            'contact_score': contact_score,
            'structure_score': structure_score,
            'formatting_score': formatting_score,
            'readability_score': readability_score,
            'contact_info': contact_info,
            'found_sections': found_sections,
            'suggestions': all_suggestions,
            'overall_feedback': self.generate_overall_feedback(overall_score),
            'word_count': word_count,
            'resume_text_preview': text[:500] + '...' if len(text) > 500 else text
        }