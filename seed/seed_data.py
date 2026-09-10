"""Seed the VitalSync PoC Firestore with recipes + one synthetic demo patient.
Run in Cloud Shell:  python3 seed/seed_data.py
(All data is synthetic — no real patients.)"""
from reset_demo import reset

if __name__ == "__main__":
    reset()
