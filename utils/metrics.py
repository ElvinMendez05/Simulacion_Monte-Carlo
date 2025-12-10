# metrics.py
def estimate_R0(cum_new_infections, cum_resolved):
    return cum_new_infections / max(1, cum_resolved)
