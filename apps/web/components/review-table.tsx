"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { analyzeReport, getReport, patchReport } from "@/lib/api";

export function ReviewTable({ reportId }: { reportId: string }): JSX.Element {
  const { t } = useTranslation();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [abnormalOnly, setAbnormalOnly] = useState(false);
  const reportQuery = useQuery({ queryKey: ["report", reportId], queryFn: () => getReport(reportId) });
  const [draft, setDraft] = useState<Record<string, number>>({});

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!reportQuery.data) {
        return;
      }
      const nextParams = reportQuery.data.extractedParams.map((param) => ({
        id: param.id,
        name: param.name,
        canonical_name: param.canonicalName,
        category: param.category,
        value: draft[param.id] ?? param.value,
        unit: param.unit,
        confidence: param.confidence,
        is_flagged: param.isFlagged,
        ref_range_key: param.refRangeKey ?? "",
        raw_reference_range: param.rawReferenceRange,
        reference_range: param.referenceRange,
        delta_from_range: param.deltaFromRange,
        note: param.note
      }));
      await patchReport(reportId, { extracted_params: nextParams });
    }
  });

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeReport(reportId),
    onSuccess: (result) => {
      router.push(`/analyses/${result.analysis_id}`);
    }
  });

  const rows = useMemo(() => {
    const items = reportQuery.data?.extractedParams ?? [];
    return items.filter((item) => {
      const matches = `${item.name} ${item.category}`.toLowerCase().includes(search.toLowerCase());
      const flagged = !abnormalOnly || item.isFlagged;
      return matches && flagged;
    });
  }, [abnormalOnly, reportQuery.data?.extractedParams, search]);

  if (reportQuery.isPending) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem" }}>Loading review data…</div></section>;
  }
  if (reportQuery.isError || !reportQuery.data) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem", color: "var(--danger)" }}>Could not load extracted parameters.</div></section>;
  }

  return (
    <section className="shell section">
      <div className="card" style={{ padding: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ marginTop: 0 }}>{t("review.title")}</h1>
            <p style={{ color: "var(--text-muted)" }}>Edit values before specialist analysis. Out-of-range values stay highlighted.</p>
          </div>
          <button className="button-primary" onClick={() => analyzeMutation.mutate()} disabled={analyzeMutation.isPending}>
            {analyzeMutation.isPending ? "Analyzing..." : t("review.submit")}
          </button>
        </div>
        <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "2fr 1fr auto", margin: "1rem 0" }}>
          <input className="input" aria-label={t("review.search")} placeholder={t("review.search")} value={search} onChange={(event) => setSearch(event.target.value)} />
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <input type="checkbox" checked={abnormalOnly} onChange={(event) => setAbnormalOnly(event.target.checked)} />
            {t("review.filter")}
          </label>
          <button className="button-secondary" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
            Save edits
          </button>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Category</th>
              <th>Value</th>
              <th>Range</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((param) => (
              <tr key={param.id} style={param.isFlagged ? { background: "rgba(233,125,53,0.08)" } : undefined}>
                <td>{param.name}</td>
                <td>{param.category}</td>
                <td>
                  <input
                    className="input"
                    aria-label={`${param.name} value`}
                    value={String(draft[param.id] ?? param.value)}
                    onChange={(event) => setDraft((previous) => ({ ...previous, [param.id]: Number(event.target.value) }))}
                  />
                </td>
                <td>{param.rawReferenceRange}</td>
                <td>{Math.round(param.confidence * 100)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
