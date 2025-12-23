# app/ml/matcher.py

import numpy as np
#from sklearn.metrics.pairwise import cosine_similarity

def build_skill_vector(user_skills, all_skills):
    vec = np.zeros(len(all_skills))
    for s in user_skills:
        idx = all_skills.index(s)
        vec[idx] = 1
    return vec

def compute_match_score(mentor_vec, mentee_vec):
    return cosine_similarity([mentor_vec], [mentee_vec])[0][0]
