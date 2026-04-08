from __future__ import annotations

from app.models import anemia, diabetes, kidney, liver, thyroid

WHO_IRON = "https://www.who.int/publications/i/item/9789241596107"
ADA_DIABETES = "https://diabetesjournals.org/care/article/47/Supplement_1/S20/153951"


def _plain_language_condition_summary(model_name: str, condition: str) -> str:
    lowered = condition.lower()
    if model_name == "anemia":
        return "The blood counts may suggest an anemia-related pattern."
    if model_name == "diabetes":
        if "prediabetes" in lowered:
            return "The blood sugar results may be a little higher than expected."
        return "The blood sugar results may need follow-up with repeat testing."
    if model_name == "kidney":
        return "The kidney-related results may need follow-up."
    if model_name == "thyroid":
        return "The thyroid results may need follow-up."
    if model_name == "liver":
        return "The liver-related results may need follow-up."
    return f"The submitted values may be related to {lowered}."


def _deviation_band(param: dict) -> str:
    delta = param.get("delta_from_range")
    if not isinstance(delta, (int, float)):
        return "mild"
    boundary = param.get("range_min") if delta < 0 else param.get("range_max")
    if not isinstance(boundary, (int, float)) or boundary == 0:
        return "moderate" if abs(delta) >= 2 else "mild"
    ratio = abs(delta) / abs(boundary)
    if ratio >= 0.25:
        return "marked"
    if ratio >= 0.1:
        return "moderate"
    return "mild"


def _format_param_finding(param: dict) -> tuple[str, str, str]:
    canonical_name = str(param.get("canonical_name", param.get("name", ""))).lower()
    value = param.get("value")
    unit = param.get("unit", "")
    status = "outside range"
    delta = param.get("delta_from_range")
    if isinstance(delta, (int, float)):
        status = "below range" if delta < 0 else "above range"
    severity = _deviation_band(param)
    reference = param.get("raw_reference_range", "not available")

    if canonical_name == "hemoglobin" and status == "below range":
        summary = "Your hemoglobin is lower than the usual range."
        explanation = (
            f"Hemoglobin is {severity}ly below the usual range at {value} {unit}. "
            "This can mean your blood may be carrying less oxygen than expected and may fit an anemia-related pattern."
        )
        note = "It may help to review iron levels, diet, bleeding history, and a repeat blood count with a clinician."
        return summary, explanation, note

    if canonical_name == "glucose" and status == "above range":
        if isinstance(value, (int, float)) and value >= 126:
            summary = "Your blood sugar is higher than the usual fasting range."
        else:
            summary = "Your blood sugar is a little higher than expected."
        explanation = (
            f"Glucose is above the usual fasting range at {value} {unit}. "
            "This may mean your body is not handling sugar normally and may need repeat testing."
        )
        note = "Check whether the sample was fasting and discuss repeat glucose or HbA1c testing with a clinician."
        return summary, explanation, note

    if canonical_name == "creatinine" and status == "above range":
        summary = "Your creatinine is higher than the usual range."
        explanation = (
            f"Creatinine is above the usual range at {value} {unit}. "
            "This can happen when the kidneys are under stress, when you are dehydrated, or when kidney function needs closer review."
        )
        note = "It may help to review hydration, medicines, blood pressure, and repeat kidney tests with a clinician."
        return summary, explanation, note

    if canonical_name == "tsh" and status == "above range":
        summary = "Your thyroid-stimulating hormone, or TSH, is higher than the usual range."
        explanation = (
            f"TSH is above the usual range at {value} {unit}. "
            "This may happen when the thyroid is working more slowly than expected and usually needs to be checked with other thyroid tests."
        )
        note = "It may help to review thyroid symptoms, free T4, and repeat thyroid tests with a clinician."
        return summary, explanation, note

    if canonical_name == "wbc":
        summary = f"Your white blood cell count is {status}."
        explanation = f"The white blood cell count is {status} at {value} {unit}. This can change with infection, inflammation, stress, medicines, or other causes."
        note = "If this stays abnormal, it may help to review symptoms and the detailed blood count with a clinician."
        return summary, explanation, note

    if canonical_name == "platelets":
        summary = f"Your platelet count is {status}."
        explanation = f"The platelet count is {status} at {value} {unit}. Platelet changes can be temporary or can need follow-up depending on bleeding, bruising, infection, and repeat results."
        note = "If this stays abnormal, discuss bleeding, bruising, recent illness, and repeat blood counts with a clinician."
        return summary, explanation, note

    explanation = (
        f"{param['name']} is {status} at {value} {unit}. "
        f"The usual range shown on this report is {reference}."
    )
    note = param.get("note") or "This result is best reviewed together with symptoms, medical history, and repeat testing if needed."
    summary = f"Your {param['name']} result is {status}."
    return summary, explanation.strip(), note


def run_specialist_models(params: dict[str, float], age: int, sex: str) -> tuple[list[dict], list[dict], list[dict], dict[str, float], str]:
    model_outputs = []
    for model_name, predictor in (
        ("anemia", anemia.predict),
        ("diabetes", diabetes.predict),
        ("kidney", kidney.predict),
        ("liver", liver.predict),
        ("thyroid", thyroid.predict),
    ):
        result = predictor(params, age, sex)
        probability = result["probability"]
        condition = result["condition"]
        if "no clear" in condition.lower():
            explanation = f"This model did not find a strong {model_name} pattern in the submitted values. Please consult a healthcare provider for full interpretation."
            summary = f"No strong {model_name} pattern was found."
        else:
            explanation = f"This model found a pattern that may be related to {condition.lower()}. Please consult a healthcare provider."
            summary = _plain_language_condition_summary(model_name, condition)
        model_outputs.append(
            {
                "model_name": model_name,
                "model_version": result["model_version"],
                "probability": probability,
                "severity": result["severity"],
                "condition": condition,
                "explanation": explanation,
                "summary": summary,
                "top_features": result["top_features"],
            }
        )

    conditions = [
        {
            "condition": output["condition"],
            "severity": output["severity"],
            "summary": output["summary"],
            "explanation": output["explanation"],
            "probability": output["probability"],
            "model_name": output["model_name"],
            "model_version": output["model_version"],
        }
        for output in model_outputs
        if "no clear" not in output["condition"].lower()
    ]
    confidence_scores = {output["model_name"]: output["probability"] for output in model_outputs}
    summary = "No clear condition signals were found." if not conditions else " ".join(item["summary"] for item in conditions[:3])
    recommendations = [
        {
            "text": "Review abnormal blood values with a licensed clinician before acting on this summary.",
            "caveat": "Thresholds are guideline-based and do not replace clinical context.",
            "sources": [{"label": "WHO anemia guidance", "href": WHO_IRON}, {"label": "ADA diabetes standards", "href": ADA_DIABETES}],
        }
    ]
    if any(item["model_name"] == "diabetes" and item["probability"] > 0.7 for item in model_outputs):
        recommendations.append(
            {
                "text": "Repeat fasting glucose or HbA1c testing may be appropriate if your clinician agrees.",
                "caveat": "Do not self-diagnose from a single report.",
                "sources": [{"label": "ADA diabetes standards", "href": ADA_DIABETES}],
            }
        )
    return model_outputs, conditions, recommendations, confidence_scores, summary


def build_detailed_report(
    summary: str,
    conditions: list[dict],
    abnormal_params: list[dict],
    specialist_models: list[dict],
    confidence_scores: dict[str, float],
) -> dict:
    findings: list[dict] = []
    finding_summaries: list[str] = []
    for param in abnormal_params:
        delta = param.get("delta_from_range")
        status = "outside range"
        if isinstance(delta, (int, float)):
            status = "below range" if delta < 0 else "above range"
        summary_text, explanation, note = _format_param_finding(param)
        finding_summaries.append(summary_text)
        findings.append(
            {
                "parameter_name": param["name"],
                "category": param.get("category", "General"),
                "status": status,
                "confidence": round(float(param.get("confidence", 0.0)) * 100, 1),
                "explanation": explanation.strip(),
                "clinical_note": note,
            }
        )

    if not findings:
        findings.append(
            {
                "parameter_name": "Overall profile",
                "category": "General",
                "status": "within reference range",
                "confidence": 90.0,
                "explanation": "No strongly abnormal extracted parameters were identified from the reviewed values.",
                "clinical_note": "Continue routine follow-up and discuss any symptoms with a healthcare provider.",
            }
        )
        finding_summaries.append("No strongly abnormal extracted parameters were identified from the reviewed values.")

    key_findings = [item["summary"] for item in conditions[:2]]
    for finding_summary in finding_summaries:
        if finding_summary not in key_findings:
            key_findings.append(finding_summary)
        if len(key_findings) >= 3:
            break
    if not key_findings and specialist_models:
        strongest = max(specialist_models, key=lambda model: model["probability"])
        key_findings.append(
            f"Top model signal: {strongest['model_name']} at {round(strongest['probability'] * 100)}% confidence."
        )

    if not key_findings:
        key_findings.append("No dominant condition pattern was detected from the extracted report values.")

    follow_up = (
        "These findings are not a diagnosis. "
        "They are a plain-language summary of what looks outside the usual range and what may be worth discussing with a qualified clinician."
    )

    overview = summary
    if not conditions and finding_summaries:
        overview = f"{finding_summaries[0]} No strong overall disease pattern was found by the models, but follow-up may still be worth considering."

    return {
        "overview": overview,
        "key_findings": key_findings,
        "parameter_findings": findings,
        "follow_up": follow_up,
    }


def build_voice_script(detailed_report: dict, language: str) -> str:
    intro = detailed_report.get("overview", "")
    findings = detailed_report.get("key_findings", [])
    parameter_findings = detailed_report.get("parameter_findings", [])
    follow_up = detailed_report.get("follow_up", "")
    lines = [intro]
    if findings:
        lines.append("Key findings: " + " ".join(findings[:3]))
    if parameter_findings:
        top_params = parameter_findings[:4]
        lines.append(
            "Parameter review: "
            + " ".join(
                f"{item['parameter_name']} is {item['status']}. {item['clinical_note']}"
                for item in top_params
            )
        )
    if follow_up:
        lines.append(follow_up)
    if language != "english":
        lines.insert(0, f"Translated summary for {language}.")
    return " ".join(segment for segment in lines if segment).strip()
