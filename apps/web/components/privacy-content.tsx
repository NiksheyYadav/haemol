"use client";

import { useQuery } from "@tanstack/react-query";

import { getPrivacy } from "@/lib/api";

export function PrivacyContent(): JSX.Element {
  const privacyQuery = useQuery({ queryKey: ["privacy"], queryFn: getPrivacy });
  if (privacyQuery.isPending) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem" }}>Loading privacy policy…</div></section>;
  }
  if (privacyQuery.isError || !privacyQuery.data) {
    return <section className="shell section"><div className="card" style={{ padding: "1.5rem", color: "var(--danger)" }}>Privacy data unavailable.</div></section>;
  }
  const policy = privacyQuery.data;
  return (
    <section className="shell section">
      <div className="card" style={{ padding: "1.5rem" }}>
        <h1 style={{ marginTop: 0 }}>Privacy</h1>
        <ul>
          <li>Files are deleted after {policy.retentionDays} days unless you delete them sooner.</li>
          <li>No data is sold or used for training without explicit consent.</li>
          <li>Encryption in transit: {policy.encryptionInTransit}</li>
          <li>Encryption at rest: {policy.encryptionAtRest}</li>
        </ul>
      </div>
    </section>
  );
}
