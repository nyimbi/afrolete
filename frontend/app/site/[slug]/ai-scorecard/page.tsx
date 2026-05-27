"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { apiRequest } from "@/lib/api";
import { apiBaseUrl } from "@/lib/config";
import type {
  AgentEthicalScorecardRead,
  AgentScorecardCommentRead,
  AgentScorecardPublicationArtifactLinkRead,
  AgentScorecardPublicationArtifactRead,
  AgentScorecardPublicationRead,
  OrganizationPublicSiteRead
} from "@/types/operations";

export default function PublicAiScorecardPage({ params }: { params: { slug: string } }) {
  const [site, setSite] = useState<OrganizationPublicSiteRead | null>(null);
  const [scorecard, setScorecard] = useState<AgentEthicalScorecardRead | null>(null);
  const [comments, setComments] = useState<AgentScorecardCommentRead[]>([]);
  const [publications, setPublications] = useState<AgentScorecardPublicationRead[]>([]);
  const [artifactLink, setArtifactLink] = useState<AgentScorecardPublicationArtifactLinkRead | null>(null);
  const [commentForm, setCommentForm] = useState({
    display_name: "",
    affiliation: "",
    contact_email: "",
    comment: "",
    consent_to_publish: true
  });
  const [error, setError] = useState("");
  const [commentError, setCommentError] = useState("");
  const [commentNotice, setCommentNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    apiRequest<OrganizationPublicSiteRead>(`/organizations/public/${encodeURIComponent(params.slug)}`)
      .then((siteData) => {
        if (cancelled) {
          return;
        }
        setSite(siteData);
        setError("");
        return Promise.all([
          apiRequest<AgentEthicalScorecardRead>(`/agents/ethical-scorecard?organization_id=${siteData.id}`),
          apiRequest<AgentScorecardCommentRead[]>(`/agents/ethical-scorecard/comments?organization_id=${siteData.id}`),
          apiRequest<AgentScorecardPublicationRead[]>(
            `/agents/ethical-scorecard/publications?organization_id=${siteData.id}`
          )
        ]);
      })
      .then((loaded) => {
        if (!cancelled && loaded) {
          const [scorecardData, commentRows, publicationRows] = loaded;
          setScorecard(scorecardData);
          setComments(commentRows);
          setPublications(publicationRows);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "AI scorecard unavailable");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [params.slug]);

  const colors = useMemo(
    () => ({
      "--site-primary": site?.brand_primary_color ?? "#0f766e",
      "--site-secondary": site?.brand_secondary_color ?? "#b7791f"
    }) as CSSProperties,
    [site?.brand_primary_color, site?.brand_secondary_color]
  );

  const displayName = site?.public_name ?? site?.name ?? "AfroLete organization";
  const latestPublication = publications[0] ?? null;

  const submitComment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!site) {
      return;
    }
    setBusy(true);
    setCommentError("");
    setCommentNotice("");
    try {
      const created = await apiRequest<AgentScorecardCommentRead>("/agents/ethical-scorecard/comments", {
        method: "POST",
        body: {
          organization_id: site.id,
          display_name: commentForm.display_name,
          affiliation: commentForm.affiliation || null,
          contact_email: commentForm.contact_email || null,
          comment: commentForm.comment,
          consent_to_publish: commentForm.consent_to_publish
        }
      });
      if (created.status === "published" && created.consent_to_publish) {
        setComments((current) => [created, ...current.filter((item) => item.id !== created.id)]);
      }
      setCommentNotice(
        created.status === "published"
          ? "Feedback published."
          : "Feedback received for operator review."
      );
      setCommentForm({
        display_name: "",
        affiliation: "",
        contact_email: "",
        comment: "",
        consent_to_publish: true
      });
    } catch (caught) {
      setCommentError(caught instanceof Error ? caught.message : "Scorecard feedback could not be submitted");
    } finally {
      setBusy(false);
    }
  };

  const downloadPublicationArtifact = async (publicationId: string, artifactFormat: "markdown" | "pdf") => {
    setBusy(true);
    setCommentError("");
    try {
      const artifact = await apiRequest<AgentScorecardPublicationArtifactRead>(
        `/agents/ethical-scorecard/publications/${publicationId}/artifact?artifact_format=${artifactFormat}`
      );
      if (artifact.content_base64) {
        downloadBase64Artifact(artifact.content_base64, artifact.content_type, artifact.download_filename);
      } else {
        downloadTextArtifact(artifact.content, artifact.content_type, artifact.download_filename);
      }
    } catch (caught) {
      setCommentError(caught instanceof Error ? caught.message : "Publication artifact could not be downloaded");
    } finally {
      setBusy(false);
    }
  };

  const createPublicationArtifactLink = async (publicationId: string, artifactFormat: "markdown" | "pdf") => {
    setBusy(true);
    setCommentError("");
    try {
      const link = await apiRequest<AgentScorecardPublicationArtifactLinkRead>(
        `/agents/ethical-scorecard/publications/${publicationId}/artifact-link?artifact_format=${artifactFormat}`
      );
      setArtifactLink(link);
    } catch (caught) {
      setCommentError(caught instanceof Error ? caught.message : "Publication link could not be created");
    } finally {
      setBusy(false);
    }
  };

  if (error) {
    return (
      <main className="public-site-page public-ai-page" style={colors}>
        <section className="public-site-shell public-ai-error">
          <div className="public-site-brand">
            <div className="mark">AL</div>
            <div>
              <strong>AfroLete</strong>
              <span>AI scorecard</span>
            </div>
          </div>
          <h1>Scorecard unavailable</h1>
          <p>{error}</p>
        </section>
      </main>
    );
  }

  if (!site || !scorecard) {
    return (
      <main className="public-site-page public-ai-page" style={colors}>
        <section className="public-site-shell public-ai-error">
          <div className="public-site-brand">
            <div className="mark">AL</div>
            <div>
              <strong>AfroLete</strong>
              <span>Loading AI scorecard</span>
            </div>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="public-site-page public-ai-page" style={colors}>
      <section className="public-ai-hero">
        <div className="public-site-shell public-ai-hero-grid">
          <div className="public-site-brand">
            {site.logo_url ? <img src={site.logo_url} alt="" /> : <div className="mark">{initials(displayName)}</div>}
            <div>
              <strong>{displayName}</strong>
              <span>Public AI accountability scorecard</span>
            </div>
          </div>
          <div className="public-ai-copy">
            <p className="section-label">Ethical AI</p>
            <h1>{displayName} AI scorecard</h1>
            <p>{scorecard.public_summary}</p>
          </div>
          <div className="public-ai-score">
            <strong>{scorecard.score}</strong>
            <span>Grade {scorecard.grade}</span>
          </div>
        </div>
      </section>

      <section className="public-site-shell public-ai-panel">
        <div className="public-ai-metrics">
          <Metric label="Approved models" value={`${scorecard.approved_models}/${scorecard.total_models}`} />
          <Metric label="Blocked models" value={scorecard.blocked_models} />
          <Metric label="Undocumented models" value={scorecard.undocumented_models} />
          <Metric label="Fairness audits" value={scorecard.bias_audits} />
          <Metric label="Passing audits" value={scorecard.passing_bias_audits} />
          <Metric label="Failing audits" value={scorecard.failing_bias_audits} />
          <Metric label="Open mitigations" value={scorecard.open_mitigations} />
          <Metric label="Open appeals" value={scorecard.pending_appeals} />
          <Metric label="Resolved appeals" value={scorecard.resolved_appeals} />
          <Metric label="Human review queue" value={scorecard.human_review_required} />
          <Metric label="Ledger status" value={scorecard.ledger_valid ? "Valid" : "Review"} />
          <Metric label="Generated" value={formatDate(scorecard.generated_at)} />
        </div>

        <div className="public-ai-actions">
          <div>
            <p className="section-label">Improvement plan</p>
            <h2>What the organization is watching</h2>
          </div>
          <div>
            {scorecard.improvement_actions.map((action) => (
              <span key={action}>{action}</span>
            ))}
          </div>
        </div>

        {latestPublication ? (
          <div className="public-ai-publication">
            <div>
              <p className="section-label">Published snapshot</p>
              <h2>{latestPublication.period_label} · {latestPublication.score}/100 · {latestPublication.grade}</h2>
              <p>{latestPublication.public_summary}</p>
            </div>
            <div>
              <span>Published {formatDate(latestPublication.published_at)}</span>
              <span>{latestPublication.published_comment_count} public comments · {latestPublication.flagged_comment_count} held for review</span>
              <span>Snapshot {latestPublication.snapshot_hash.slice(0, 16)}</span>
              <button type="button" onClick={() => downloadPublicationArtifact(latestPublication.id, "markdown")} disabled={busy}>
                Download Markdown
              </button>
              <button type="button" onClick={() => downloadPublicationArtifact(latestPublication.id, "pdf")} disabled={busy}>
                Download PDF
              </button>
              <button type="button" onClick={() => createPublicationArtifactLink(latestPublication.id, "pdf")} disabled={busy}>
                Share PDF
              </button>
              {artifactLink ? (
                <a href={`${apiBaseUrl}${artifactLink.signed_url}`} target="_blank" rel="noreferrer">
                  Open shared artifact
                </a>
              ) : null}
            </div>
          </div>
        ) : null}

        <div className="public-ai-comments">
          <div>
            <p className="section-label">Public comments</p>
            <h2>Community feedback</h2>
            <div className="public-ai-comment-list">
              {comments.map((comment) => (
                <article key={comment.id}>
                  <strong>{comment.display_name}</strong>
                  <span>{comment.affiliation ?? "Community member"} · {formatDate(comment.submitted_at)}</span>
                  <p>{comment.comment}</p>
                </article>
              ))}
              {comments.length === 0 ? <span>No public comments yet</span> : null}
            </div>
          </div>
          <form onSubmit={submitComment}>
            <label>
              Name
              <input
                value={commentForm.display_name}
                onChange={(event) => setCommentForm({ ...commentForm, display_name: event.target.value })}
                required
              />
            </label>
            <label>
              Affiliation
              <input
                value={commentForm.affiliation}
                onChange={(event) => setCommentForm({ ...commentForm, affiliation: event.target.value })}
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={commentForm.contact_email}
                onChange={(event) => setCommentForm({ ...commentForm, contact_email: event.target.value })}
              />
            </label>
            <label>
              Comment
              <textarea
                value={commentForm.comment}
                onChange={(event) => setCommentForm({ ...commentForm, comment: event.target.value })}
                required
              />
            </label>
            <label className="public-ai-checkbox">
              <input
                type="checkbox"
                checked={commentForm.consent_to_publish}
                onChange={(event) => setCommentForm({ ...commentForm, consent_to_publish: event.target.checked })}
              />
              Publish this comment
            </label>
            {commentNotice ? <p className="form-success">{commentNotice}</p> : null}
            {commentError ? <p className="form-error">{commentError}</p> : null}
            <button type="submit" disabled={busy}>{busy ? "Sending" : "Submit feedback"}</button>
          </form>
        </div>

        <div className="public-ai-footer">
          <a href={`/site/${encodeURIComponent(site.slug)}`}>Organization site</a>
          <span>Published through AfroLete governance records</span>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

function initials(value: string): string {
  return value
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString();
}

function downloadTextArtifact(content: string, contentType: string, filename: string) {
  const blob = new Blob([content], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function downloadBase64Artifact(contentBase64: string, contentType: string, filename: string) {
  const raw = window.atob(contentBase64);
  const bytes = new Uint8Array(raw.length);
  for (let index = 0; index < raw.length; index += 1) {
    bytes[index] = raw.charCodeAt(index);
  }
  const blob = new Blob([bytes], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
