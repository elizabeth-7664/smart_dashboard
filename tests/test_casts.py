# test_casts.py
from datetime import datetime
from dateutil import parser

def to_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        print("to_int parse failed for:", repr(val))
        return 0

def to_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        print("to_float parse failed for:", repr(val))
        return 0.0

def to_str(val):
    return str(val).strip() if val not in (None, "") else ""

def to_date(val):
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
        try:
            return parser.parse(val).date()
        except Exception:
            print("to_date parse failed for:", repr(val))
            return None

tests = [
    ("10", "20.5", " Soap ", "2025-01-02"),
    ("", "N/A", None, "2/1/2025"),
    ("ten", "12.3.4", "Product", "2025-01-02 08:00"),
    (None, None, "", ""),
]

for a,b,c,d in tests:
    print("to_int:", a, "->", to_int(a))
    print("to_float:", b, "->", to_float(b))
    print("to_str:", c, "->", repr(to_str(c)))
    print("to_date:", d, "->", to_date(d))
    print("---")
