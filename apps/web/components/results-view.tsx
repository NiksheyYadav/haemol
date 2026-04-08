"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { getAnalysis, getAudio, requestAudio, submitFeedback } from "@/lib/api";

const LANGUAGES = ["hindi", "tamil", "telugu", "kannada", "malayalam", "bengali", "marathi", "gujarati", "punjabi", "english"];

export function ResultsView({ analysisId }: { analysisId: string }): JSX.Element {
  const { t } = useTranslation();
  const analysisQuery = useQuery({ queryKey: ["analysis", analysisId], queryFn: () => getAnalysis(analysisId) });
  const [language, setLanguage] = useState("english");
  const [showText, setShowText] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const requestedLanguagesRef = useRef<Set<string>>(new Set());
  const audioMutation = useMutation({
    mutationFn: async (requestedLanguage: string) => {
      await requestAudio(analysisId, requestedLanguage);
      const audio = await getAudio(analysisId, requestedLanguage);
      return { language: requestedLanguage, ...audio };
    }
  });
  const feedbackMutation = useMutation({
    mutationFn: (sentiment: "up" | "down") => submitFeedback(analysisId, { sentiment, text: feedbackText || undefined })
  });

  const topModel = useMemo(() => {
    const models = analysisQuery.data?.specialistModels ?? [];
    return [...models].sort((left, right) => right.probability - left.probability)[0];
  }, [analysisQuery.data?.specialistModels]);

  const latestAudioJob = analysisQuery.data
    ? [...analysisQuery.data.audioJobs]
        .filter((job) => job.language === language)
        .sort((left, right) => new Date(right.createdAt).getTime() - new Date(left.createdAt).getTime())[0]
    : undefined;

  useEffect(() => {
    if (!analysisQuery.data || requestedLanguagesRef.current.has(language) || latestAudioJob) {
      return;
    }
    requestedLanguagesRef.current.add(language);
    audioMutation.mutate(language);
  }, [analysisQuery.data, audioMutation, language, latestAudioJob]);

  if (analysisQuery.isPending) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem" }}>Loading analysis…</div></section>;
  }
  if (analysisQuery.isError || !analysisQuery.data) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem", color: "var(--danger)" }}>Analysis could not be loaded.</div></section>;
  }

  const analysis = analysisQuery.data;
  const audio = audioMutation.data?.language === language
    ? audioMutation.data
    : latestAudioJob
      ? {
          language,
          status: latestAudioJob.status,
          audio_url: latestAudioJob.audioUrl ?? null,
          fallback_text: latestAudioJob.fallbackText ?? null
        }
      : undefined;

  return (
    <section className="shell section">
      <div className="grid">
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
          <div className="card" style={{ padding: "1.25rem" }}>
            <p>Conditions detected</p>
            <strong>{analysis.conditions.length}</strong>
          </div>
          <div className="card" style={{ padding: "1.25rem" }}>
            <p>Top model</p>
            <strong>{topModel?.modelName ?? "Pending"}</strong>
          </div>
          <div className="card" style={{ padding: "1.25rem" }}>
            <p>Abnormal count</p>
            <strong>{analysis.abnormalParams.length}</strong>
          </div>
        </div>

        <div className="card" style={{ padding: "1.5rem" }}>
          <h1 style={{ marginTop: 0 }}>{t("results.title")}</h1>
          <p>{analysis.summary}</p>
          <div className="grid" style={{ marginTop: "1rem" }}>
            {analysis.conditions.map((condition) => (
              <details key={`${condition.modelName}-${condition.condition}`} open>
                <summary>
                  {condition.condition} · {Math.round(condition.probability * 100)}%
                </summary>
                <p>{condition.explanation}</p>
              </details>
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: "1.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "start", flexWrap: "wrap" }}>
            <div>
              <h2 style={{ marginTop: 0, marginBottom: "0.5rem" }}>{t("results.report.title")}</h2>
              <p style={{ margin: 0, color: "var(--text-muted)" }}>{analysis.detailedReport.overview}</p>
            </div>
            <div className="badge">{analysis.detailedReport.parameterFindings.length} findings</div>
          </div>
          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginTop: "1rem" }}>
            <div className="card" style={{ padding: "1rem" }}>
              <h3 style={{ marginTop: 0 }}>{t("results.report.keyFindings")}</h3>
              <ul style={{ marginBottom: 0 }}>
                {analysis.detailedReport.keyFindings.map((item, index) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="card" style={{ padding: "1rem" }}>
              <h3 style={{ marginTop: 0 }}>{t("results.report.followUp")}</h3>
              <p style={{ marginBottom: 0 }}>{analysis.detailedReport.followUp}</p>
            </div>
          </div>
          <div className="grid" style={{ marginTop: "1rem" }}>
            {analysis.detailedReport.parameterFindings.map((finding) => (
              <article key={`${finding.parameterName}-${finding.category}`} className="card" style={{ padding: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "center", flexWrap: "wrap" }}>
                  <div>
                    <h3 style={{ margin: 0 }}>{finding.parameterName}</h3>
                    <p style={{ margin: "0.3rem 0 0", color: "var(--text-muted)" }}>{finding.category}</p>
                  </div>
                  <div className="badge">{finding.confidence}% confidence</div>
                </div>
                <p style={{ marginBottom: "0.75rem" }}>{finding.explanation}</p>
                <p style={{ margin: 0, color: "var(--text-muted)" }}>{finding.clinicalNote}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: "1.5rem" }}>
          <h2 style={{ marginTop: 0 }}>Specialist models</h2>
          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            {analysis.specialistModels.map((model) => (
              <div key={`${model.modelName}-${model.modelVersion}`} className="card" style={{ padding: "1rem" }}>
                <div className="badge">{model.severity}</div>
                <h3>{model.modelName}</h3>
                <p>{model.explanation}</p>
                <div style={{ height: "8px", background: "var(--surface-muted)", borderRadius: "999px", overflow: "hidden" }}>
                  <div style={{ width: `${Math.round(model.probability * 100)}%`, height: "100%", background: "linear-gradient(90deg, var(--primary), var(--accent))" }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: "1.5rem" }}>
          <h2 style={{ marginTop: 0 }}>Abnormal parameters</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Value</th>
                <th>Range</th>
                <th>Delta</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              {analysis.abnormalParams.map((param) => (
                <tr key={param.id}>
                  <td>{param.name}</td>
                  <td>
                    {param.value} {param.unit}
                  </td>
                  <td>{param.rawReferenceRange}</td>
                  <td>{param.deltaFromRange ?? "0"}</td>
                  <td>{param.note ?? "Review with clinician"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card" style={{ padding: "1.5rem" }}>
          <h2 style={{ marginTop: 0 }}>Recommendations</h2>
          <ul>
            {analysis.recommendations.map((item, index) => (
              <li key={`${item.text}-${index}`}>
                <strong>{item.text}</strong>
                <p>{item.caveat}</p>
                <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                  {item.sources.map((source) => (
                    <a key={source.href} href={source.href} target="_blank" rel="noreferrer">
                      {source.label}
                    </a>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="card" style={{ padding: "1.5rem" }}>
          <h2 style={{ marginTop: 0 }}>{t("audio.title")}</h2>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <select className="select" aria-label="Audio language" value={language} onChange={(event) => setLanguage(event.target.value)}>
              {LANGUAGES.map((entry) => (
                <option key={entry} value={entry}>
                  {entry}
                </option>
              ))}
            </select>
            <button className="button-primary" onClick={() => audioMutation.mutate(language)} disabled={audioMutation.isPending}>
              {audioMutation.isPending ? t("audio.generating") : t("audio.generate")}
            </button>
            <button className="button-secondary" onClick={() => setShowText((current) => !current)}>
              {t("audio.showText")}
            </button>
          </div>
          {audio?.audio_url ? (
            <audio key={audio.audio_url} style={{ width: "100%", marginTop: "1rem" }} controls preload="metadata" src={audio.audio_url} />
          ) : (
            <p style={{ color: "var(--text-muted)" }}>{audio?.fallback_text ?? t("audio.waiting")}</p>
          )}
          {showText ? <p>{audio?.fallback_text ?? analysis.detailedReport.overview}</p> : null}
        </div>

        <div className="card" style={{ padding: "1.5rem" }}>
          <h2 style={{ marginTop: 0 }}>Feedback</h2>
          <textarea
            className="textarea"
            rows={3}
            placeholder={t("results.feedback.placeholder")}
            value={feedbackText}
            onChange={(event) => setFeedbackText(event.target.value)}
          />
          <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.75rem" }}>
            <button className="button-secondary" onClick={() => feedbackMutation.mutate("up")}>
              {t("results.feedback.good")}
            </button>
            <button className="button-secondary" onClick={() => feedbackMutation.mutate("down")}>
              {t("results.feedback.bad")}
            </button>
          </div>
          <a href={`/reports/${analysis.reportId}/review`} style={{ display: "inline-block", marginTop: "1rem" }}>
            Report incorrect extraction
          </a>
        </div>
      </div>
    </section>
  );
}
