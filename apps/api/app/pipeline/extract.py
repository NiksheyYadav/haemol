from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass

from app.services.reference_data import canonical_name, reference_range_for

logger = logging.getLogger(__name__)

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None

try:
    import spacy
except ImportError:  # pragma: no cover
    spacy = None


_NLP = None


@dataclass
class Param:
    name: str
    canonical_name: str
    value: float
    unit: str
    confidence: float
    category: str
    range_min: float | None
    range_max: float | None
    raw_reference_range: str
    delta_from_range: float | None
    is_flagged: bool
    ref_range_key: str
    note: str | None = None


TARGET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("hemoglobin", re.compile(r"(?:hemoglobin|hb|hgb)\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
    ("wbc", re.compile(r"(?:wbc|white blood cell(?: count)?)\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
    ("rbc", re.compile(r"(?:rbc|red blood cell(?: count)?)\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
    ("platelets", re.compile(r"(?:platelets|plt)\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
    ("glucose", re.compile(r"(?:glucose|blood sugar|fbs)\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
    ("hba1c", re.compile(r"(?:hba1c|a1c)\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
    ("creatinine", re.compile(r"creatinine\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
    ("alt", re.compile(r"(?:alt|sgpt)\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
    ("ast", re.compile(r"(?:ast|sgot)\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
    ("tsh", re.compile(r"tsh\s*[:=-]?\s*(\d+(?:\.\d+)?)", re.I)),
]
GENERIC_PATTERN = re.compile(
    r"([a-zA-Z][a-zA-Z0-9\s/_\-\(\)%]{1,48})\s*[:=\-|]\s*([<>]?\s*\d+(?:,\d{3})*(?:\.\d+)?)\s*([a-zA-Z/%\^0-9]+)?",
    re.I,
)
TYPO_FIXES = {
    "haemoglobin": "hemoglobin",
    "heamoglobin": "hemoglobin",
    "platelates": "platelets",
    "creatnine": "creatinine",
    "bilirubin totai": "bilirubin total",
}


def parse_pdf(file_bytes: bytes) -> str:
    if pdfplumber is None:
        logger.warning("pdfplumber unavailable; PDF parsing skipped")
        return ""
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text:
                pages.append(page_text)
            for table in page.extract_tables() or []:
                for row in table:
                    clean = [str(cell).strip() for cell in row if cell]
                    if clean:
                        pages.append(" | ".join(clean))
    return "\n".join(pages)


def ocr_image(file_bytes: bytes) -> str:
    if pytesseract is None or Image is None:
        logger.warning("OCR dependencies unavailable; OCR skipped")
        return ""
    image = Image.open(io.BytesIO(file_bytes)).convert("L")
    return pytesseract.image_to_string(image, config="--oem 3 --psm 6")


def normalize_text(text: str) -> str:
    normalized = text.lower().replace("μ", "u").replace("µ", "u").replace("\t", " ")
    normalized = re.sub(r"[ ]{2,}", " ", normalized)
    normalized = normalized.replace("\r", "\n")
    for typo, fix in TYPO_FIXES.items():
        normalized = normalized.replace(typo, fix)
    return normalized


def _load_nlp():
    global _NLP
    if _NLP is not None:
        return _NLP
    if spacy is None:
        return None
    try:
        _NLP = spacy.load("en_core_web_sm")
    except Exception:
        return None
    return _NLP


def extract_params(text: str) -> list[Param]:
    found: dict[str, Param] = {}
    cleaned = normalize_text(text)
    for canonical, pattern in TARGET_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            value = float(match.group(1))
            found[canonical] = _build_param(canonical, canonical, value, "")

    for match in GENERIC_PATTERN.finditer(cleaned):
        name, raw_value, unit = match.groups()
        canonical = canonical_name(name)
        value = float(raw_value.replace(",", "").replace("<", "").replace(">", "").strip())
        if canonical not in found:
            found[canonical] = _build_param(name.strip(), canonical, value, unit or "")

    nlp = _load_nlp()
    if nlp is not None:
        try:
            doc = nlp(cleaned)
            for ent in doc.ents:
                if ent.label_ not in {"CARDINAL", "QUANTITY", "PERCENT"}:
                    continue
                preceding = cleaned[max(0, ent.start_char - 48): ent.start_char]
                name_tokens = preceding.split()
                if not name_tokens:
                    continue
                label = " ".join(name_tokens[-3:])
                canonical = canonical_name(label)
                if canonical in found:
                    continue
                raw = ent.text.replace(",", "").replace("%", "")
                try:
                    value = float(raw)
                except ValueError:
                    continue
                found[canonical] = _build_param(label, canonical, value, "%" if ent.label_ == "PERCENT" else "")
        except Exception:
            logger.exception("spaCy extraction failed")
    return list(found.values())


def canonicalize(params: list[Param]) -> list[Param]:
    canonicalized: dict[str, Param] = {}
    for param in params:
        canonicalized[param.canonical_name] = _build_param(param.name, canonical_name(param.canonical_name), param.value, param.unit)
    return list(canonicalized.values())


def score_confidence(param: Param) -> float:
    confidence = 0.55
    if param.unit:
        confidence += 0.1
    if param.range_min is not None or param.range_max is not None:
        confidence += 0.15
    if param.name.lower() == param.canonical_name.lower():
        confidence += 0.1
    if param.value >= 0:
        confidence += 0.05
    return min(round(confidence, 2), 0.98)


def _build_param(name: str, canonical: str, value: float, unit: str) -> Param:
    low, high, default_unit, category = reference_range_for(canonical, "male", 30)
    resolved_unit = unit or default_unit
    delta = None
    flagged = False
    if low is not None and value < low:
        delta = round(value - low, 2)
        flagged = True
    elif high is not None and value > high:
        delta = round(value - high, 2)
        flagged = True
    reference_string = f"{low}–{high} {resolved_unit}".strip() if low is not None or high is not None else ""
    param = Param(
        name=name.strip(),
        canonical_name=canonical,
        value=value,
        unit=resolved_unit,
        confidence=0.0,
        category=category,
        range_min=low,
        range_max=high,
        raw_reference_range=reference_string,
        delta_from_range=delta,
        is_flagged=flagged,
        ref_range_key=f"{canonical}:{category.lower()}",
    )
    param.confidence = score_confidence(param)
    return param
