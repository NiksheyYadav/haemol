from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RangeRule:
    unit: str
    category: str
    both: tuple[float, float] | None = None
    male: tuple[float, float] | None = None
    female: tuple[float, float] | None = None
    adult_senior: tuple[float, float] | None = None


REFERENCE_RANGES: dict[str, RangeRule] = {
    "hemoglobin": RangeRule(unit="g/dL", category="CBC", male=(13.5, 17.5), female=(12.0, 15.5)),
    "wbc": RangeRule(unit="10^3/uL", category="CBC", both=(4.0, 11.0)),
    "rbc": RangeRule(unit="10^6/uL", category="CBC", male=(4.5, 5.9), female=(4.1, 5.1)),
    "platelets": RangeRule(unit="10^3/uL", category="CBC", both=(150.0, 450.0)),
    "hematocrit": RangeRule(unit="%", category="CBC", male=(41.0, 53.0), female=(36.0, 46.0)),
    "mcv": RangeRule(unit="fL", category="CBC", both=(80.0, 100.0)),
    "mch": RangeRule(unit="pg", category="CBC", both=(27.0, 33.0)),
    "mchc": RangeRule(unit="g/dL", category="CBC", both=(32.0, 36.0)),
    "rdw": RangeRule(unit="%", category="CBC", both=(11.5, 14.5)),
    "glucose": RangeRule(unit="mg/dL", category="Metabolic", both=(70.0, 99.0)),
    "hba1c": RangeRule(unit="%", category="HbA1c", both=(4.0, 5.6)),
    "creatinine": RangeRule(unit="mg/dL", category="Kidney", male=(0.7, 1.3), female=(0.5, 1.1), adult_senior=(0.7, 1.4)),
    "blood urea nitrogen": RangeRule(unit="mg/dL", category="Kidney", both=(7.0, 25.0)),
    "sodium": RangeRule(unit="mEq/L", category="Metabolic", both=(136.0, 145.0)),
    "potassium": RangeRule(unit="mEq/L", category="Metabolic", both=(3.5, 5.1)),
    "alt": RangeRule(unit="U/L", category="Liver", male=(7.0, 56.0), female=(7.0, 45.0)),
    "ast": RangeRule(unit="U/L", category="Liver", both=(10.0, 40.0)),
    "alkaline phosphatase": RangeRule(unit="U/L", category="Liver", both=(44.0, 147.0)),
    "albumin": RangeRule(unit="g/dL", category="Liver", both=(3.5, 5.0)),
    "total bilirubin": RangeRule(unit="mg/dL", category="Liver", both=(0.2, 1.2)),
    "direct bilirubin": RangeRule(unit="mg/dL", category="Liver", both=(0.0, 0.3)),
    "tsh": RangeRule(unit="mIU/L", category="Thyroid", both=(0.4, 4.0)),
    "t3": RangeRule(unit="ng/dL", category="Thyroid", both=(80.0, 200.0)),
    "t4": RangeRule(unit="ug/dL", category="Thyroid", both=(5.0, 12.0)),
    "iron": RangeRule(unit="ug/dL", category="Iron", male=(65.0, 175.0), female=(50.0, 170.0)),
    "ferritin": RangeRule(unit="ng/mL", category="Iron", male=(20.0, 500.0), female=(20.0, 200.0)),
    "cholesterol": RangeRule(unit="mg/dL", category="Lipids", both=(0.0, 200.0)),
    "hdl": RangeRule(unit="mg/dL", category="Lipids", male=(40.0, 60.0), female=(50.0, 60.0)),
    "ldl": RangeRule(unit="mg/dL", category="Lipids", both=(0.0, 130.0)),
    "triglycerides": RangeRule(unit="mg/dL", category="Lipids", both=(0.0, 150.0)),
}

ALIASES = {
    "hb": "hemoglobin",
    "hgb": "hemoglobin",
    "white blood cells": "wbc",
    "red blood cells": "rbc",
    "plt": "platelets",
    "bun": "blood urea nitrogen",
    "sgpt": "alt",
    "sgot": "ast",
    "bilirubin total": "total bilirubin",
    "bilirubin direct": "direct bilirubin",
}


def canonical_name(name: str) -> str:
    normalized = " ".join(name.lower().replace("_", " ").split())
    return ALIASES.get(normalized, normalized)


def reference_range_for(name: str, sex: str, age: int) -> tuple[float | None, float | None, str, str]:
    canon = canonical_name(name)
    rule = REFERENCE_RANGES.get(canon)
    if rule is None:
        return None, None, "", "General"
    if age >= 65 and rule.adult_senior:
        low, high = rule.adult_senior
    elif sex.lower() == "female" and rule.female:
        low, high = rule.female
    elif sex.lower() == "male" and rule.male:
        low, high = rule.male
    elif rule.both:
        low, high = rule.both
    else:
        low, high = (None, None)
    return low, high, rule.unit, rule.category
