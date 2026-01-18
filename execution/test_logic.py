from utils import calculate_next_business_slot
from datetime import datetime
import os

def test_scheduling():
    os.environ['COMM_START_HOUR'] = '10'
    os.environ['COMM_END_HOUR'] = '22'
    
    # Case 1: Within window
    t1 = datetime(2026, 1, 14, 12, 0)
    res1 = calculate_next_business_slot(t1, 5)
    print(f"12:00 + 5h = {res1} (Expected: 17:00)")
    
    # Case 2: After end hour
    t2 = datetime(2026, 1, 14, 20, 0)
    res2 = calculate_next_business_slot(t2, 5)
    print(f"20:00 + 5h = {res2} (Expected: Next day 10:00)")
    
    # Case 3: Before start hour
    t3 = datetime(2026, 1, 14, 8, 0)
    res3 = calculate_next_business_slot(t3, 1)
    print(f"08:00 + 1h = {res3} (Expected: Today 10:00)")

if __name__ == "__main__":
    test_scheduling()
