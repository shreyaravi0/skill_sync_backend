# app/ml/advanced_matcher.py
"""
Advanced Matching Algorithm for SkillSync
Uses semantic embeddings + multi-factor scoring instead of simple cosine similarity
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class AdvancedSkillMatcher:
    """
    Hybrid matching algorithm combining:
    1. Semantic skill embeddings (captures skill relationships)
    2. Multi-factor scoring (skill overlap, complementarity, diversity)
    3. Experience-based weighting
    4. Skill proficiency awareness
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize with a pre-trained sentence transformer model
        
        Args:
            model_name: Hugging Face model name for semantic embeddings
                       Options: 'all-MiniLM-L6-v2' (fast, 384-dim)
                               'all-mpnet-base-v2' (better quality, 768-dim)
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded semantic model: {model_name}")
        except Exception as e:
            logger.warning(f"Failed to load semantic model: {e}. Falling back to basic matching.")
            self.model = None
        
        # Weights for different scoring components
        self.weights = {
            'semantic_similarity': 0.40,   # How related are their skills?
            'skill_complementarity': 0.25, # Do they have complementary skills?
            'experience_match': 0.20,      # Experience level compatibility
            'skill_diversity': 0.15        # Diversity of skill overlap
        }
    
    def encode_skills(self, skills: List[str]) -> np.ndarray:
        """
        Convert list of skills to semantic embedding
        
        Args:
            skills: List of skill names (e.g., ['Python', 'Machine Learning'])
        
        Returns:
            Semantic embedding vector (384 or 768 dimensions)
        """
        if not skills:
            # Return zero vector if no skills
            return np.zeros(384)
        
        if self.model is None:
            # Fallback to basic bag-of-words if model failed to load
            return self._basic_encoding(skills)
        
        # Join skills into a sentence for better context
        skills_text = ", ".join(skills)
        
        try:
            embedding = self.model.encode(skills_text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error encoding skills: {e}")
            return self._basic_encoding(skills)
    
    def _basic_encoding(self, skills: List[str]) -> np.ndarray:
        """Fallback to simple one-hot encoding if semantic model fails"""
        # This is just for safety - should rarely be used
        return np.array([hash(skill) % 100 for skill in skills[:10]])
    
    def compute_semantic_similarity(self, 
                                   embedding1: np.ndarray, 
                                   embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Returns:
            Similarity score in [0, 1]
        """
        if embedding1.shape != embedding2.shape:
            return 0.0
        
        # Reshape for sklearn
        sim = cosine_similarity([embedding1], [embedding2])[0][0]
        
        # Normalize to [0, 1] (cosine similarity is in [-1, 1])
        return (sim + 1) / 2
    
    def compute_skill_complementarity(self,
                                     user_skills: List[str],
                                     target_skills: List[str]) -> float:
        """
        Measure how complementary the skills are
        
        Complementarity = skills the target has that the user doesn't
        (Important for mentorship: mentor should have skills mentee lacks)
        
        Returns:
            Complementarity score in [0, 1]
        """
        if not user_skills or not target_skills:
            return 0.0
        
        user_set = set(s.lower() for s in user_skills)
        target_set = set(s.lower() for s in target_skills)
        
        # Skills target has that user doesn't
        complementary_skills = target_set - user_set
        
        # Normalize by target's total skills
        complementarity = len(complementary_skills) / len(target_set)
        
        return complementarity
    
    def compute_skill_diversity(self,
                               user_skills: List[str],
                               target_skills: List[str]) -> float:
        """
        Measure diversity of overlapping skills
        
        High diversity = many different areas of overlap
        Low diversity = overlap in only one area
        
        Returns:
            Diversity score in [0, 1]
        """
        if not user_skills or not target_skills:
            return 0.0
        
        user_set = set(s.lower() for s in user_skills)
        target_set = set(s.lower() for s in target_skills)
        
        # Overlapping skills
        overlap = user_set & target_set
        
        if not overlap:
            return 0.0
        
        # Measure diversity using normalized overlap ratio
        # Penalize if all overlap is in one area vs. spread across many
        total_unique = len(user_set | target_set)
        overlap_ratio = len(overlap) / total_unique
        
        # Diversity bonus for having moderate overlap (not too little, not too much)
        # Bell curve centered at 0.3 overlap ratio
        diversity = 1.0 - abs(0.3 - overlap_ratio) / 0.7
        diversity = max(0.0, diversity)
        
        return diversity
    
    def compute_experience_match(self,
                                user_experience: str,
                                target_experience: str,
                                role: str) -> float:
        """
        Compute compatibility based on experience levels
        
        For mentorship:
        - Mentor should be MORE experienced than mentee
        - But not TOO much more (for effective communication)
        
        Args:
            user_experience: User's experience level (e.g., "Beginner", "Intermediate")
            target_experience: Target's experience level
            role: "mentor" or "mentee"
        
        Returns:
            Experience match score in [0, 1]
        """
        # Map experience levels to numeric scale
        experience_map = {
            'beginner': 1,
            'junior': 2,
            'intermediate': 3,
            'senior': 4,
            'expert': 5,
            'advanced': 5,
            '': 3  # Default to intermediate if not specified
        }
        
        user_exp = experience_map.get(user_experience.lower(), 3)
        target_exp = experience_map.get(target_experience.lower(), 3)
        
        if role == "mentee":
            # Mentee matching with mentor
            # Ideal: mentor is 1-2 levels above mentee
            diff = target_exp - user_exp
            
            if diff < 0:
                # Mentor less experienced - poor match
                return 0.3
            elif diff == 1:
                # Perfect - one level above
                return 1.0
            elif diff == 2:
                # Good - two levels above
                return 0.9
            elif diff == 3:
                # Okay - three levels above
                return 0.6
            else:
                # Too big a gap
                return 0.4
        
        else:
            # Mentor matching with mentee
            # Similar logic, but reversed
            diff = user_exp - target_exp
            
            if diff < 0:
                return 0.3
            elif diff == 1:
                return 1.0
            elif diff == 2:
                return 0.9
            elif diff == 3:
                return 0.6
            else:
                return 0.4
    
    def compute_match_score(self,
                          user_skills: List[str],
                          target_skills: List[str],
                          user_experience: str = "",
                          target_experience: str = "",
                          role: str = "mentee") -> Dict[str, float]:
        """
        Compute comprehensive match score using all factors
        
        Args:
            user_skills: List of user's skill names
            target_skills: List of target's skill names
            user_experience: User's experience level
            target_experience: Target's experience level
            role: User's role ("mentor" or "mentee")
        
        Returns:
            Dictionary with total score and component scores
        """
        # Component 1: Semantic similarity
        user_embedding = self.encode_skills(user_skills)
        target_embedding = self.encode_skills(target_skills)
        semantic_score = self.compute_semantic_similarity(user_embedding, target_embedding)
        
        # Component 2: Skill complementarity
        complementarity_score = self.compute_skill_complementarity(user_skills, target_skills)
        
        # Component 3: Experience match
        experience_score = self.compute_experience_match(
            user_experience, target_experience, role
        )
        
        # Component 4: Skill diversity
        diversity_score = self.compute_skill_diversity(user_skills, target_skills)
        
        # Weighted combination
        total_score = (
            self.weights['semantic_similarity'] * semantic_score +
            self.weights['skill_complementarity'] * complementarity_score +
            self.weights['experience_match'] * experience_score +
            self.weights['skill_diversity'] * diversity_score
        )
        
        return {
            'total': total_score,
            'semantic_similarity': semantic_score,
            'skill_complementarity': complementarity_score,
            'experience_match': experience_score,
            'skill_diversity': diversity_score
        }
    
    def generate_explanation(self,
                           scores: Dict[str, float],
                           user_skills: List[str],
                           target_skills: List[str]) -> str:
        """
        Generate human-readable explanation for the match
        
        Args:
            scores: Score dictionary from compute_match_score
            user_skills: User's skills
            target_skills: Target's skills
        
        Returns:
            Explanation string
        """
        # Find strongest matching factor
        components = {
            'semantic_similarity': 'strong skill alignment',
            'skill_complementarity': 'complementary skill sets',
            'experience_match': 'compatible experience levels',
            'skill_diversity': 'diverse skill overlap'
        }
        
        # Get top 2 factors
        factor_scores = [(k, scores[k]) for k in components.keys()]
        factor_scores.sort(key=lambda x: x[1], reverse=True)
        
        top_factors = [components[f[0]] for f in factor_scores[:2] if f[1] > 0.5]
        
        # Find overlapping skills
        user_set = set(s.lower() for s in user_skills)
        target_set = set(s.lower() for s in target_skills)
        overlap = user_set & target_set
        
        explanation = f"Match confidence: {scores['total']:.0%}"
        
        if top_factors:
            explanation += f" (based on {', '.join(top_factors)})"
        
        if overlap:
            # Limit to 3 skills for brevity
            overlap_list = list(overlap)[:3]
            overlap_str = ', '.join(overlap_list)
            if len(overlap) > 3:
                overlap_str += f" and {len(overlap) - 3} more"
            explanation += f". Shared interests: {overlap_str}"
        
        return explanation


# Global instance (singleton pattern)
_matcher_instance = None

def get_matcher() -> AdvancedSkillMatcher:
    """Get or create global matcher instance"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = AdvancedSkillMatcher()
    return _matcher_instance