# agent/confidence.py

def compute_confidence(load_percent, fuel_ok, traffic_score):
    score = 1.0

    if load_percent > 85:
        score *= 0.8
    if not fuel_ok:
        score *= 0.6

    score *= traffic_score
    return round(score, 2)
