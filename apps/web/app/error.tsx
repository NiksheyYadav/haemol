"use client";

export default function GlobalError({
  error,
  reset
}: {
  error: Error;
  reset: () => void;
}): JSX.Element {
  return (
    <section className="shell section">
      <div className="card" style={{ padding: "1.5rem", borderColor: "var(--danger)", color: "var(--danger)" }}>
        <h1>Something went wrong</h1>
        <p>{error.message}</p>
        <button className="button-primary" onClick={reset}>
          Try again
        </button>
      </div>
    </section>
  );
}
