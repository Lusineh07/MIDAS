#training/rules_teacher.py
CLASSES = ["NO_ACTION", "IRON_CONDOR", "DEBIT_CALL", "DEBIT_PUT", "COVERED_CALL"]

def label_one(f):
    sent_mean = f["sent_mean"]; sent_std = f["sent_std"]
    r1 = f["r_1m"]; r5 = f["r_5m"]
    above = bool(f["above_sma20"])
    mins = f["mins_since_news"]; rv = f["rv20"]
    earn = bool(f["earnings_soon"]); liq = bool(f["liquidity_flag"])

    if not liq or rv < 0.05 or (abs(sent_mean) < 0.05 and sent_std > 0.20) or (mins > 360 and abs(r5) < 0.002):
        return "NO_ACTION"
    
    trend_up = above and r5 > 0 and sent_mean > 0.10 and 0.05 <= rv <= 0.25
    trend_down = (not above) and r5 < 0 and sent_mean < -0.10 and 0.05 <= rv <= 0
    if trend_up: return "DEBIT_CALL"
    if trend_down: return "DEBIT_PUT"

    if 0.10 <= rv <= 0.30 and abs(r1) < 0.005 and abs(r5) < 0.003 and not earn:
        return "IRON_CONDOR"
    
    if (-0.05 <= sent_mean <= 0.15) and 0.20 <= rv <= 0.60 and above and not earn:
        return "COVERED_CALL"
    
    #tie-breakers
    if abs(r5) >= 0.006 or abs(r1) >= 0.01:
        return "DEBIT_CALL" if r5 > 0 else "DEBIT_PUT"
    
    return "IRON_CONDOR" if above else "COVERED_CALL"