"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { analyzeReport, getReport } from "@/lib/api";

const orderedSteps = ["queued", "parsing", "ocr", "nlp_extraction", "done"];

export function StatusView({ reportId }: { reportId: string }): JSX.Element {
  const router = useRouter();
  const reportQuery = useQuery({
    queryKey: ["report", reportId],
    queryFn: () => getReport(reportId),
    refetchInterval: (query) => (query.state.data?.extractionStep === "done" ? false : 1500)
  });

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeReport(reportId),
    onSuccess: (data) => {
      router.push(`/analyses/${data.analysis_id}`);
    }
  });

  useEffect(() => {
    const report = reportQuery.data;
    if (!report) return;
    if (report.extractionStep === "done" && !report.analysisId && !analyzeMutation.isPending && !analyzeMutation.isSuccess) {
      analyzeMutation.mutate();
    }
    if (report.analysisId) {
      router.push(`/analyses/${report.analysisId}`);
    }
  }, [reportQuery.data, analyzeMutation, router, reportId]);

  if (reportQuery.isPending) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem" }}>Loading extraction status…</div></section>;
  }
  if (reportQuery.isError || !reportQuery.data) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem", color: "var(--danger)" }}>Extraction status could not be loaded.</div></section>;
  }
  const report = reportQuery.data;
  const currentIndex = orderedSteps.indexOf(report.extractionStep);
  return (
    <section className="shell section">
      <div className="card" style={{ padding: "1.5rem" }}>
        <h1 style={{ marginTop: 0 }}>Extraction status</h1>
        <p>Report ID: {report.id}</p>
        <div className="progress-steps">
          {orderedSteps.map((step, index) => (
            <div
              key={step}
              className="step"
              data-state={index < currentIndex ? "done" : index === currentIndex ? "active" : "idle"}
            >
              {step.replace("_", " ")}
            </div>
          ))}
        </div>
        {report.errorMessage ? (
          <div className="card" style={{ padding: "1rem", borderColor: "var(--danger)", color: "var(--danger)", marginTop: "1rem" }}>
            {report.errorMessage}
          </div>
        ) : null}
        <div style={{ display: "flex", gap: "0.75rem", marginTop: "1.5rem", flexWrap: "wrap" }}>
          <Link className="button-secondary" href="/upload">
            Retry upload
          </Link>
          {report.extractionStep === "done" ? (
            <Link className="button-primary" href={report.analysisId ? `/analyses/${report.analysisId}` : `/reports/${report.id}/review`}>
              {report.analysisId ? "View results" : "Review extracted parameters"}
            </Link>
          ) : null}
        </div>
      </div>
    </section>
  );
}
