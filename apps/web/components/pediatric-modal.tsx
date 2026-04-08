"use client";

import { useTranslation } from "react-i18next";

export function PediatricModal({
  open,
  onContinue
}: {
  open: boolean;
  onContinue: () => void;
}): JSX.Element | null {
  const { t } = useTranslation();
  if (!open) {
    return null;
  }
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="pediatric-title">
      <div className="card" style={{ width: "min(32rem, calc(100vw - 2rem))", padding: "1.5rem" }}>
        <h2 id="pediatric-title" style={{ marginTop: 0 }}>
          {t("disclaimer.pediatric.title")}
        </h2>
        <p>{t("disclaimer.pediatric.body")}</p>
        <button className="button-primary" onClick={onContinue}>
          Continue
        </button>
      </div>
    </div>
  );
}
