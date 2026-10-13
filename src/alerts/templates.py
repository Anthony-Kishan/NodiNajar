"""
Fixed alert templates (project rule: no AI writes alerts). The same wording is
used by the web app (webapp/lib/alerts.ts) and the API. Only measured numbers
are filled in.
"""
from __future__ import annotations

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def bn_digits(x) -> str:
    return str(x).translate(BN_DIGITS)


def alert_text(seg: dict, days: int, lang: str = "bn") -> str:
    m = round(seg["retreat_m"])
    high = seg["level"] == "red"
    if lang == "bn":
        return (f"নদীনজর সতর্কবার্তা: গত {bn_digits(days)} দিনে আপনার এলাকায় যমুনার পাড় {bn_digits(m)} মিটার সরে এসেছে। "
                f"ভাঙনের ঝুঁকি: {'উচ্চ' if high else 'মাঝারি'}। মূল্যবান জিনিস ও গবাদিপশু নিরাপদ স্থানে সরানোর প্রস্তুতি নিন "
                f"এবং ইউনিয়ন পরিষদের সাথে যোগাযোগ করুন। ({seg['id']})")
    if lang == "en":
        return (f"NodiNajar alert: in the last {days} days the Jamuna bank near you moved {m} m. Erosion risk: "
                f"{'HIGH' if high else 'MEDIUM'}. Prepare to move valuables and livestock to safety and contact your "
                f"union parishad. ({seg['id']})")
    raise ValueError("lang must be 'bn' or 'en'")


def audience(level: str) -> list[str]:
    if level == "red":
        return ["families within 200 m (SMS + voice)", "union parishad", "upazila office", "Water Development Board"]
    return ["officials and NGOs"]
