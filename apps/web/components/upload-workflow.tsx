"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { createFileReport, createTextReport, sendEvent } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { PediatricModal } from "@/components/pediatric-modal";

const PARAM_OPTIONS = [
  "Hemoglobin",
  "WBC",
  "RBC",
  "Platelets",
  "Glucose",
  "HbA1c",
  "Creatinine",
  "ALT",
  "AST",
  "TSH",
  "T3",
  "T4",
  "Iron",
  "Ferritin",
  "Cholesterol",
  "HDL",
  "LDL",
  "Triglycerides"
];

type Mode = "file" | "text" | "manual";

export function UploadWorkflow(): JSX.Element {
  const { t } = useTranslation();
  const router = useRouter();
  const pediatricAcknowledged = useAppStore((state) => state.pediatricAcknowledged);
  const acknowledgePediatric = useAppStore((state) => state.acknowledgePediatric);
  const [mode, setMode] = useState<Mode>("file");
  const [file, setFile] = useState<File | null>(null);
  const [sex, setSex] = useState("male");
  const [age, setAge] = useState(30);
  const [consent, setConsent] = useState(false);
  const [rawText, setRawText] = useState("");
  const [manualRows, setManualRows] = useState([{ name: "Hemoglobin", value: "", unit: "g/dL" }]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showPediatric, setShowPediatric] = useState(false);

  const manualParams = useMemo(() => {
    const result: Record<string, number> = {};
    for (const row of manualRows) {
      const parsed = Number(row.value);
      if (row.name && Number.isFinite(parsed)) {
        result[row.name] = parsed;
      }
    }
    return result;
  }, [manualRows]);

  async function handleSubmit(): Promise<void> {
    setError(null);
    if (age < 18 && !pediatricAcknowledged) {
      setShowPediatric(true);
      return;
    }
    if (!consent) {
      setError("Consent is required before continuing.");
      return;
    }
    setSubmitting(true);
    try {
      let reportId = "";
      if (mode === "file") {
        if (!file) {
          throw new Error("Please choose a file.");
        }
        if (file.size > 10 * 1024 * 1024) {
          throw new Error("File exceeds 10MB.");
        }
        const formData = new FormData();
        formData.set("file", file);
        formData.set("locale", "en");
        formData.set("sex", sex);
        formData.set("age", String(age));
        formData.set("consent_given", String(consent));
        const report = await createFileReport(formData);
        reportId = report.id;
      } else if (mode === "text") {
        const report = await createTextReport({
          source_type: "text",
          locale: "en",
          sex,
          age,
          consent_given: consent,
          raw_text: rawText
        });
        reportId = report.id;
      } else {
        const report = await createTextReport({
          source_type: "manual",
          locale: "en",
          sex,
          age,
          consent_given: consent,
          raw_text: Object.entries(manualParams)
            .map(([key, value]) => `${key}: ${value}`)
            .join("\n"),
          manual_params: manualParams
        });
        reportId = report.id;
      }
      await sendEvent({ name: "upload_succeeded", payload: { mode }, report_id: reportId });
      router.push(`/reports/${reportId}`);
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : "Submission failed");
      await sendEvent({ name: "upload_failed", payload: { mode } });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PediatricModal
        open={showPediatric}
        onContinue={() => {
          acknowledgePediatric();
          setShowPediatric(false);
        }}
      />
      <section className="shell section">
        <div className="hero">
          <span className="badge">Safer AI workflow</span>
          <h1>{t("upload.title")}</h1>
          <p>{t("brand.tagline")}</p>
        </div>
        <div className="grid two-col">
          <div className="card" style={{ padding: "1.5rem" }}>
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem", flexWrap: "wrap" }}>
              {(["file", "text", "manual"] as Mode[]).map((tab) => (
                <button
                  key={tab}
                  className={tab === mode ? "button-primary" : "button-secondary"}
                  onClick={() => setMode(tab)}
                  aria-pressed={tab === mode}
                >
                  {tab === "file" ? t("upload.fileTab") : tab === "text" ? t("upload.textTab") : t("upload.manualTab")}
                </button>
              ))}
            </div>
            <div className="grid" style={{ gap: "1rem" }}>
              <label>
                <span>{t("upload.gender")}</span>
                <select aria-label={t("upload.gender")} className="select" value={sex} onChange={(event) => setSex(event.target.value)}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </label>
              <label>
                <span>{t("upload.age")}</span>
                <input aria-label={t("upload.age")} className="input" type="number" value={age} onChange={(event) => setAge(Number(event.target.value))} />
              </label>
              {mode === "file" ? (
                <label className="card" style={{ padding: "1.2rem", borderStyle: "dashed", textAlign: "center" }}>
                  <span style={{ display: "block", marginBottom: "0.75rem" }}>{t("upload.dropzone")}</span>
                  <input
                    aria-label="Upload file"
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg,.txt"
                    onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  />
                  {file ? <p>{file.name}</p> : null}
                </label>
              ) : null}
              {mode === "text" ? (
                <textarea aria-label="Pasted blood report text" className="textarea" rows={14} value={rawText} onChange={(event) => setRawText(event.target.value)} />
              ) : null}
              {mode === "manual" ? (
                <div className="grid">
                  <datalist id="parameter-list">
                    {PARAM_OPTIONS.map((option) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                  {manualRows.map((row, index) => (
                    <div key={`${row.name}-${index}`} style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "2fr 1fr 1fr" }}>
                      <input
                        list="parameter-list"
                        className="input"
                        aria-label={`Parameter ${index + 1}`}
                        value={row.name}
                        onChange={(event) => {
                          const next = [...manualRows];
                          next[index] = { ...next[index], name: event.target.value };
                          setManualRows(next);
                        }}
                      />
                      <input
                        className="input"
                        aria-label={`Value ${index + 1}`}
                        value={row.value}
                        onChange={(event) => {
                          const next = [...manualRows];
                          next[index] = { ...next[index], value: event.target.value };
                          setManualRows(next);
                        }}
                      />
                      <input
                        className="input"
                        aria-label={`Unit ${index + 1}`}
                        value={row.unit}
                        onChange={(event) => {
                          const next = [...manualRows];
                          next[index] = { ...next[index], unit: event.target.value };
                          setManualRows(next);
                        }}
                      />
                    </div>
                  ))}
                  <button className="button-ghost" onClick={() => setManualRows([...manualRows, { name: "", value: "", unit: "" }])}>
                    Add parameter
                  </button>
                </div>
              ) : null}
              <label style={{ display: "flex", alignItems: "start", gap: "0.6rem" }}>
                <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} aria-label={t("upload.consent")} />
                <span>{t("upload.consent")}</span>
              </label>
              {error ? <div className="card" style={{ padding: "1rem", borderColor: "var(--danger)", color: "var(--danger)" }}>{error}</div> : null}
              <button className="button-primary" onClick={() => void handleSubmit()} disabled={submitting}>
                {submitting ? "Submitting..." : t("upload.submit")}
              </button>
            </div>
          </div>
          <div className="grid">
            <div className="card" style={{ padding: "1.5rem" }}>
              <h2 style={{ marginTop: 0 }}>Why v3 feels different</h2>
              <ul>
                <li>Extraction, review, and analysis are separate steps.</li>
                <li>Age and sex are captured before reference ranges are applied.</li>
                <li>Each condition uses guarded “may indicate” language.</li>
                <li>Hindi UI and 10-language audio are available from day one.</li>
              </ul>
            </div>
            <div className="card" style={{ padding: "1.5rem" }}>
              <h2 style={{ marginTop: 0 }}>What happens next</h2>
              <div className="progress-steps">
                <div className="step" data-state="active">Parsing</div>
                <div className="step">OCR</div>
                <div className="step">NLP Extraction</div>
                <div className="step">Review</div>
                <div className="step">Analysis</div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
