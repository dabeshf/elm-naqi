"""
generate_sample_data.py
------------------------
Creates a realistic but SYNTHETIC customer-records dataset with deliberately
injected data-quality problems, so Naqi's checks visibly fire in a demo.

All data is fake (randomly generated). No real personal data is used.
Run:  python generate_sample_data.py
Output: sample_data.csv
"""

import random
import csv
from datetime import datetime, timedelta

random.seed(42)

FIRST_EN = ["Mohammed", "Ahmad", "Fahad", "Abdullah", "Sara", "Noura", "Reem",
            "Khalid", "Faisal", "Layla", "Huda", "Omar", "Yousef", "Maha", "Aisha"]
LAST_EN = ["Al-Ahmad", "Al-Otaibi", "Al-Qahtani", "Al-Ghamdi", "Al-Harbi",
           "Al-Dossari", "Al-Shammari", "Al-Zahrani", "Al-Malki", "Al-Mutairi"]
FIRST_AR = ["محمد", "أحمد", "فهد", "عبدالله", "سارة", "نورة", "ريم",
            "خالد", "فيصل", "ليلى", "هدى", "عمر", "يوسف", "مها", "عائشة"]
LAST_AR = ["الأحمد", "العتيبي", "القحطاني", "الغامدي", "الحربي",
           "الدوسري", "الشمري", "الزهراني", "المالكي", "المطيري"]
CITIES = ["Riyadh", "Jeddah", "Dammam", "Mecca", "Medina", "Khobar", "Tabuk"]
HEALTH = ["", "Diabetes", "Hypertension", "None", "Asthma"]  # sensitive PII
STATUS = ["Active", "Inactive", "Suspended"]


def saudi_id():
    # Saudi IDs start with 1 (citizen) or 2 (resident), 10 digits total
    return str(random.choice([1, 2])) + "".join(str(random.randint(0, 9)) for _ in range(9))


def saudi_phone():
    return "05" + str(random.randint(0, 9)) + "".join(str(random.randint(0, 9)) for _ in range(7))


def iban():
    return "SA" + "".join(str(random.randint(0, 9)) for _ in range(22))


def make_email(fn, ln, uid):
    return f"{fn.lower()}.{ln.replace('Al-', '').lower()}{uid}@example.com"


def random_date(start_year=2015, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


rows = []
for i in range(1, 481):
    idx = random.randint(0, len(FIRST_EN) - 1)
    fn, ln = FIRST_EN[idx], LAST_EN[random.randint(0, len(LAST_EN) - 1)]
    fn_ar = FIRST_AR[idx]
    ln_ar = LAST_AR[random.randint(0, len(LAST_AR) - 1)]
    reg = random_date(2018, 2023)
    last = reg + timedelta(days=random.randint(0, 1500))
    rows.append({
        "customer_id": f"C{i:04d}",
        "national_id": saudi_id(),
        "full_name_en": f"{fn} {ln}",
        "full_name_ar": f"{fn_ar} {ln_ar}",
        "email": make_email(fn, ln, i),
        "phone": saudi_phone(),
        "iban": iban(),
        "city": random.choice(CITIES),
        "registration_date": reg.strftime("%Y-%m-%d"),
        "last_activity_date": last.strftime("%Y-%m-%d"),
        "health_condition": random.choice(HEALTH),
        "account_status": random.choice(STATUS),
    })

# ---- Inject quality problems -------------------------------------------------

# 1) Exact duplicate rows (Uniqueness)
for _ in range(15):
    rows.append(dict(random.choice(rows[:400])))

# 2) Near-duplicate names (same person, different spelling) (Uniqueness/Integrity)
for _ in range(12):
    base = dict(random.choice(rows[:400]))
    variants = [
        base["full_name_en"].replace("Mohammed", "Muhammad").replace("Ahmad", "Ahmed"),
        base["full_name_en"].replace("Al-", "El-"),
        base["full_name_en"].replace(" ", "  "),
    ]
    base["full_name_en"] = random.choice(variants)
    base["customer_id"] = f"C{random.randint(9000, 9999)}"
    rows.append(base)

# 3) Missing values (Completeness)
for r in random.sample(rows, 60):
    field = random.choice(["email", "phone", "city", "full_name_ar", "national_id"])
    r[field] = ""

# 4) Invalid formats (Validity / Conformity)
for r in random.sample(rows, 45):
    which = random.choice(["email", "phone", "national_id", "iban"])
    if which == "email":
        r["email"] = r["email"].replace("@", "_at_")
    elif which == "phone":
        r["phone"] = r["phone"][:5]  # too short
    elif which == "national_id":
        r["national_id"] = str(random.randint(100, 999))  # not 10 digits
    else:
        r["iban"] = "SA123"  # too short

# 5) Stale records: very old last activity (Timeliness / Storage Limitation)
for r in random.sample(rows, 50):
    old = random_date(2013, 2016)
    r["last_activity_date"] = old.strftime("%Y-%m-%d")

# 6) Inconsistent casing / formats in city (Consistency)
for r in random.sample(rows, 70):
    if r["city"]:
        r["city"] = random.choice([r["city"].upper(), r["city"].lower(),
                                    r["city"] + " ", " " + r["city"]])

# 7) Mixed date formats (Consistency)
for r in random.sample(rows, 40):
    try:
        d = datetime.strptime(r["registration_date"], "%Y-%m-%d")
        r["registration_date"] = d.strftime("%d/%m/%Y")
    except ValueError:
        pass

random.shuffle(rows)

with open("sample_data.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote sample_data.csv with {len(rows)} rows and injected quality issues.")
