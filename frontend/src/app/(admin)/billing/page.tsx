"use client";

import { useEffect, useState } from "react";

import { apiFetch, type Paginated } from "@/lib/api";

interface Plan {
  id: string;
  name: string;
  code: string;
  price: string;
  billing_period: string;
  features: Record<string, unknown>;
  quotas: Record<string, unknown>;
  is_active: boolean;
}

interface Subscription {
  id: string;
  plan: Plan;
  status: string;
  current_period_start: string;
  current_period_end: string;
  auto_renew: boolean;
}

interface UsageRecord {
  feature_key: string;
  count: number;
  period_date: string;
}

export default function BillingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const [planCode, setPlanCode] = useState("");
  const [phone, setPhone] = useState("");
  const [method, setMethod] = useState<"ecocash" | "onemoney">("ecocash");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadAll() {
    const [plansRes, subscriptionRes, usageRes] = await Promise.all([
      apiFetch<Paginated<Plan>>("/api/v1/billing/plans/"),
      apiFetch<Subscription | null>("/api/v1/billing/subscription/"),
      apiFetch<UsageRecord[]>("/api/v1/billing/usage/"),
    ]);
    setPlans(plansRes.results);
    setSubscription(subscriptionRes);
    setUsage(usageRes);
    setLoading(false);
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time fetch on mount
    loadAll();
  }, []);

  async function handleSubscribe(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      const res = await apiFetch<{ instructions: string }>("/api/v1/billing/subscribe/", {
        method: "POST",
        body: JSON.stringify({ plan_code: planCode, phone, method }),
      });
      setMessage(res.instructions || "Payment initiated. Follow the prompt on your phone.");
      await loadAll();
    } catch {
      setError("Could not start payment. Check the phone number and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel() {
    await apiFetch("/api/v1/billing/cancel/", { method: "POST" });
    await loadAll();
  }

  if (loading) return <p className="text-gray-400">Loading…</p>;

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-xl font-semibold">Billing</h1>

      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Current Subscription
        </h2>
        {subscription ? (
          <div className="space-y-1 text-sm">
            <p>
              <span className="font-medium">{subscription.plan.name}</span> ·{" "}
              {subscription.status}
            </p>
            <p className="text-gray-500">
              Renews {new Date(subscription.current_period_end).toLocaleDateString()}
            </p>
            <button
              onClick={handleCancel}
              className="mt-2 rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50"
            >
              Cancel subscription
            </button>
          </div>
        ) : (
          <p className="text-gray-400">No active subscription.</p>
        )}
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Usage Today
        </h2>
        {usage.length === 0 ? (
          <p className="text-gray-400">No usage recorded today.</p>
        ) : (
          <ul className="space-y-1 text-sm">
            {usage.map((u) => (
              <li key={u.feature_key} className="flex justify-between">
                <span>{u.feature_key}</span>
                <span className="font-medium">{u.count}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <form
        onSubmit={handleSubscribe}
        className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
      >
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
          Subscribe to a plan
        </h2>
        {message && <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{message}</p>}
        {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Plan</label>
          <select
            required
            value={planCode}
            onChange={(e) => setPlanCode(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">Select a plan</option>
            {plans.map((p) => (
              <option key={p.id} value={p.code}>
                {p.name} — ${p.price} / {p.billing_period}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Mobile money number</label>
          <input
            type="text"
            required
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Method</label>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value as "ecocash" | "onemoney")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="ecocash">EcoCash</option>
            <option value="onemoney">OneMoney</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {submitting ? "Submitting..." : "Subscribe"}
        </button>
      </form>
    </div>
  );
}
