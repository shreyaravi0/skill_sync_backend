# app/ml/matcher.py
from sklearn.metrics.pairwise import cosine_similarity

def build_skill_vector(user_skills, all_skills):
    """
    Convert a list of user skills into a binary vector
    based on the list of all skills.
    """
    return [1 if skill in user_skills else 0 for skill in all_skills]

def compute_match_score(mentee_vec, mentor_vec):
    """
    Compute cosine similarity between two skill vectors.
    """
    return cosine_similarity([mentee_vec], [mentor_vec])[0][0]
