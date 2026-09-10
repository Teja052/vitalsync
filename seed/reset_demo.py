"""Seed / reset demo data in Firestore (used by CLI / Cloud Shell).
Complies strictly with all allergen and exclusion rules:
- demo-ramesh: Telangana, exclusions=["Egg", "All meat"], allergens=["Nuts"] (ZERO nuts/peanuts/almonds/eggs/meat)
- demo-lakshmi: Tamil Nadu, exclusions=["Beef", "Pork"], allergens=[] (ZERO beef/pork)
- demo-ananya: Karnataka, invited
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from seed_demo import run_reset

if __name__ == "__main__":
    res = run_reset()
    print(res)
