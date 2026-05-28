"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { apiRequest } from "@/lib/api";
import type {
  CommercialInvoiceCheckoutSettlementRead,
  CommercialInvoiceHostedCheckoutRead,
  CommercialInvoiceProviderCheckoutRead,
  EventTravelFeeCheckoutSettlementRead,
  EventTravelFeeHostedCheckoutRead
} from "@/types/operations";

type HostedCheckoutRead = EventTravelFeeHostedCheckoutRead | CommercialInvoiceHostedCheckoutRead;
type HostedCheckoutSettlementRead = EventTravelFeeCheckoutSettlementRead | CommercialInvoiceCheckoutSettlementRead;
type CheckoutKind = "travel" | "commercial";

export default function HostedPaymentPage() {
  return (
    <Suspense fallback={<PaymentLoading />}>
      <HostedPaymentExperience />
    </Suspense>
  );
}

function HostedPaymentExperience() {
  const params = useParams<{ sessionId: string }>();
  const searchParams = useSearchParams();
  const invoiceId = searchParams.get("invoice_id") ?? "";
  const provider = searchParams.get("provider") ?? "manual_gateway";
  const checkoutKind: CheckoutKind = searchParams.get("kind") === "commercial" ? "commercial" : "travel";
  const [checkout, setCheckout] = useState<HostedCheckoutRead | null>(null);
  const [providerSession, setProviderSession] = useState<CommercialInvoiceProviderCheckoutRead | null>(null);
  const [settlement, setSettlement] = useState<HostedCheckoutSettlementRead | null>(null);
  const [method, setMethod] = useState("mobile_money");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!params.sessionId || !invoiceId) {
      setError("Payment session link is missing invoice context.");
      return;
    }
    const checkoutPath =
      checkoutKind === "commercial"
        ? `/commercial/invoice-checkout-sessions/${encodeURIComponent(params.sessionId)}?invoice_id=${encodeURIComponent(invoiceId)}&provider=${encodeURIComponent(provider)}`
        : `/events/travel-fee-checkout-sessions/${encodeURIComponent(params.sessionId)}?invoice_id=${encodeURIComponent(invoiceId)}&provider=${encodeURIComponent(provider)}`;
    apiRequest<HostedCheckoutRead>(
      checkoutPath
    )
      .then((data) => {
        if (!cancelled) {
          setCheckout(data);
          setError("");
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Payment session unavailable");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [checkoutKind, invoiceId, params.sessionId, provider]);

  const displayAmount = useMemo(() => {
    if (!checkout) {
      return "";
    }
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: checkout.currency
    }).format(Number(checkout.open_amount));
  }, [checkout]);

  const settle = async () => {
    if (!checkout) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const settlementPath =
        checkoutKind === "commercial"
          ? `/commercial/invoice-checkout-sessions/${encodeURIComponent(checkout.session_id)}/settle`
          : `/events/travel-fee-checkout-sessions/${encodeURIComponent(checkout.session_id)}/settle`;
      const result = await apiRequest<HostedCheckoutSettlementRead>(
        settlementPath,
        {
          method: "POST",
          body: {
            invoice_id: checkout.invoice_id,
            provider: checkout.provider,
            amount: checkout.open_amount,
            currency: checkout.currency,
            method,
            status: "succeeded",
            external_payment_id: `hosted_${checkout.session_id}_${Date.now()}`,
            raw_reference: "Hosted AfroLete payment page confirmation."
          }
        }
      );
      setSettlement(result);
      setCheckout({
        ...checkout,
        amount_paid: result.amount_paid,
        open_amount: result.open_amount,
        status: result.invoice_status,
        session_status: result.session_status
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Payment could not be recorded");
    } finally {
      setBusy(false);
    }
  };

  const openProviderCheckout = async () => {
    if (!checkout || checkoutKind !== "commercial") {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const session = await apiRequest<CommercialInvoiceProviderCheckoutRead>(
        `/commercial/invoice-checkout-sessions/${encodeURIComponent(checkout.session_id)}/provider-session?invoice_id=${encodeURIComponent(checkout.invoice_id)}&provider=${encodeURIComponent(checkout.provider)}`,
        {
          method: "POST",
          body: {
            success_url: window.location.href,
            cancel_url: window.location.href,
            payment_method: method
          }
        }
      );
      setProviderSession(session);
      if (session.mode !== "local" && !session.failure_reason) {
        window.location.assign(session.redirect_url);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Provider checkout could not be created");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="payment-page">
      <section className="payment-shell">
        <div className="payment-brand">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>{checkoutKind === "commercial" ? "Secure sponsor invoice portal" : "Secure travel fee portal"}</span>
          </div>
        </div>

        {error ? <p className="payment-error">{error}</p> : null}

        {checkout ? (
          <div className="payment-grid">
            <article className="payment-summary">
              <p className="section-label">{checkout.provider}</p>
              <h1>{checkout.title}</h1>
              <p>{checkout.memo ?? checkout.checkout_summary}</p>
              <dl>
                <div>
                  <dt>Invoice</dt>
                  <dd>{checkout.invoice_number}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{checkout.session_status}</dd>
                </div>
                <div>
                  <dt>Due</dt>
                  <dd>{checkout.due_on ?? "on receipt"}</dd>
                </div>
              </dl>
            </article>

            <article className="payment-panel">
              <span>Outstanding</span>
              <strong>{displayAmount}</strong>
              <label>
                Payment method
                <select value={method} onChange={(event) => setMethod(event.target.value)}>
                  {checkout.payment_methods.map((paymentMethod) => (
                    <option key={paymentMethod} value={paymentMethod}>
                      {paymentMethod.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </label>
              <button type="button" onClick={settle} disabled={busy || checkout.session_status === "paid"}>
                {checkout.session_status === "paid" ? "Paid" : busy ? "Recording" : "Confirm payment"}
              </button>
              {checkoutKind === "commercial" ? (
                <button type="button" className="secondary" onClick={openProviderCheckout} disabled={busy || checkout.session_status === "paid"}>
                  {busy ? "Preparing" : "Provider checkout"}
                </button>
              ) : null}
              {settlement ? <p className="payment-result">{settlement.message}</p> : null}
              {providerSession ? (
                <p className="payment-result">
                  {providerSession.failure_reason ?? `Provider session ${providerSession.provider_session_id} ready`}
                </p>
              ) : null}
              <small>{checkout.client_reference}</small>
            </article>
          </div>
        ) : !error ? (
          <PaymentLoading />
        ) : null}
      </section>
    </main>
  );
}

function PaymentLoading() {
  return (
    <div className="payment-loading">
      <span>Loading payment session</span>
    </div>
  );
}
