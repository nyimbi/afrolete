"use client";

import { type FormEvent, useState } from "react";
import { apiRequest } from "@/lib/api";
import type { ActivityConsentRead, ConsentStatus } from "@/types/operations";

export default function ConsentCapturePage({ params }: { params: { token: string } }) {
  const [status, setStatus] = useState<ConsentStatus>("granted");
  const [guardianName, setGuardianName] = useState("");
  const [notes, setNotes] = useState("");
  const [result, setResult] = useState<ActivityConsentRead | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const consent = await apiRequest<ActivityConsentRead>("/safeguarding/consents/by-token", {
        method: "POST",
        body: {
          token: params.token,
          status,
          consent_text: `${guardianName || "Guardian"} responded ${status}.`,
          response_payload: JSON.stringify({ guardianName }),
          notes
        }
      });
      setResult(consent);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Consent capture failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="consent-page">
      <section className="consent-shell">
        <div className="consent-brand">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Guardian response</span>
          </div>
        </div>

        {result ? (
          <div className="consent-result">
            <p className="section-label">Recorded</p>
            <h1>{result.status === "granted" ? "Consent granted" : "Response recorded"}</h1>
            <dl>
              <div>
                <dt>Consent</dt>
                <dd>{result.id}</dd>
              </div>
              <div>
                <dt>Scope</dt>
                <dd>{result.scope_type}</dd>
              </div>
              <div>
                <dt>Channel</dt>
                <dd>{result.capture_channel}</dd>
              </div>
            </dl>
          </div>
        ) : (
          <form className="consent-form" onSubmit={submit}>
            <p className="section-label">Participation consent</p>
            <h1>Guardian decision</h1>
            <label>
              Guardian name
              <input value={guardianName} onChange={(event) => setGuardianName(event.target.value)} />
            </label>
            <label>
              Decision
              <select value={status} onChange={(event) => setStatus(event.target.value as ConsentStatus)}>
                <option value="granted">Grant consent</option>
                <option value="denied">Deny consent</option>
              </select>
            </label>
            <label>
              Notes
              <textarea value={notes} onChange={(event) => setNotes(event.target.value)} />
            </label>
            {error ? <p className="form-error">{error}</p> : null}
            <button type="submit" disabled={busy}>
              {busy ? "Recording" : "Submit"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}
