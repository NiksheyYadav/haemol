import Link from "next/link";

export default function HomePage(): JSX.Element {
  return (
    <section className="shell section">
      <div className="hero">
        <span className="badge">Biomarkly</span>
        <h1>Biomarker intelligence for clearer blood report decisions.</h1>
        <p>
          Upload PDFs, images, pasted text, or manual values. Biomarkly turns noisy lab reports into a patient-friendly,
          review-first summary with specialist models and multilingual voice guidance.
        </p>
        <div className="stats">
          <div className="card" style={{ padding: "1rem" }}>
            <strong>5 specialist models</strong>
            <p>Anemia, diabetes, kidney, liver, thyroid</p>
          </div>
          <div className="card" style={{ padding: "1rem" }}>
            <strong>10 audio languages</strong>
            <p>Sarvam AI with text fallback</p>
          </div>
          <div className="card" style={{ padding: "1rem" }}>
            <strong>Review before diagnosis</strong>
            <p>Editable parameter validation layer</p>
          </div>
        </div>
        <div style={{ display: "flex", gap: "0.75rem", marginTop: "2rem", flexWrap: "wrap" }}>
          <Link className="button-primary" href="/upload">
            Start with a report
          </Link>
          <Link className="button-secondary" href="/about">
            See model details
          </Link>
        </div>
      </div>
    </section>
  );
}
