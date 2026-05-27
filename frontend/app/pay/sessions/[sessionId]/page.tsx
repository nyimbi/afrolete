"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { apiRequest } from "@/lib/api";
import type {
  EventTravelFeeCheckoutSettlementRead,
  EventTravelFeeHostedCheckoutRead
} from "@/types/operations";

export default function TravelFeePaymentPage() {
  return (
    <Suspense fallback={<PaymentLoading />}>
      <TravelFeePaymentExperience />
    </Suspense>
  );
}

function TravelFeePaymentExperience() {
  const params = useParams<{ sessionId: string }>();
  const searchParams = useSearchParams();
  const invoiceId = searchParams.get("invoice_id") ?? "";
  const provider = searchParams.get("provider") ?? "manual_gateway";
  const [checkout, setCheckout] = useState<EventTravelFeeHostedCheckoutRead | null>(null);
  const [settlement, setSettlement] = useState<EventTravelFeeCheckoutSettlementRead | null>(null);
  const [method, setMethod] = useState("mobile_money");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!params.sessionId || !invoiceId) {
      setError("Payment session link is missing invoice context.");
      return;
    }
    apiRequest<EventTravelFeeHostedCheckoutRead>(
      `/events/travel-fee-checkout-sessions/${encodeURIComponent(params.sessionId)}?invoice_id=${encodeURIComponent(invoiceId)}&provider=${encodeURIComponent(provider)}`
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
  }, [invoiceId, params.sessionId, provider]);

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
      const result = await apiRequest<EventTravelFeeCheckoutSettlementRead>(
        `/events/travel-fee-checkout-sessions/${encodeURIComponent(checkout.session_id)}/settle`,
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

  return (
    <main className="payment-page">
      <section className="payment-shell">
        <div className="payment-brand">
          <div className="mark">AL</div>
          <div>
            <strong>AfroLete</strong>
            <span>Secure travel fee portal</span>
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
              {settlement ? <p className="payment-result">{settlement.message}</p> : null}
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
