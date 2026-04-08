"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { getAbout } from "@/lib/api";

type Tab = "models" | "pipeline" | "data";

export function AboutContent(): JSX.Element {
  const [tab, setTab] = useState<Tab>("models");
  const aboutQuery = useQuery({ queryKey: ["about"], queryFn: getAbout });

  if (aboutQuery.isPending) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem" }}>Loading about data…</div></section>;
  }
  if (aboutQuery.isError || !aboutQuery.data) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem", color: "var(--danger)" }}>About data unavailable.</div></section>;
  }

  const about = aboutQuery.data;
  return (
    <section className="shell section">
      <div className="card" style={{ padding: "1.5rem" }}>
        <h1 style={{ marginTop: 0 }}>About Biomarkly</h1>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
          <button className={tab === "models" ? "button-primary" : "button-secondary"} onClick={() => setTab("models")}>
            Models
          </button>
          <button className={tab === "pipeline" ? "button-primary" : "button-secondary"} onClick={() => setTab("pipeline")}>
            Pipeline
          </button>
          <button className={tab === "data" ? "button-primary" : "button-secondary"} onClick={() => setTab("data")}>
            Training Data
          </button>
        </div>
        {tab === "models" ? (
          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
            {about.models.map((model) => (
              <div key={model.name} className="card" style={{ padding: "1rem" }}>
                <strong>{model.name}</strong>
                <p>F1: {model.f1}</p>
                <p>Version: {model.version}</p>
              </div>
            ))}
          </div>
        ) : null}
        {tab === "pipeline" ? (
          <ul>
            {about.pipeline.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : null}
        {tab === "data" ? (
          <ul>
            {about.trainingData.map((item) => (
              <li key={item.name}>
                {item.name}: {item.size}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  );
}
