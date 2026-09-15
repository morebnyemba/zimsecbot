"use client";

import { useEffect, useState } from "react";
import { Activity, Check, CreditCard, Wallet } from "lucide-react";

import { apiFetch, type Paginated } from "@/lib/api";
import type { Plan, Subscription, UsageRecord } from "@/lib/types";

export default function BillingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageRecord[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [phone, setPhone] = useState("");
  const [method, setMethod] = useState<"ecocash" | "onemoney">("ecocash");
  const [submitting, setSubmitting] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadAll() {
    const [plansRes, subscriptionRes, usageRes] = await Promise.all([
      apiFetch<Paginated<Plan>>("/api/v1/billing/plans/"),
      apiFetch<Subscription | undefined>("/api/v1/billing/subscription/"),
      apiFetch<UsageRecord[]>("/api/v1/billing/usage/"),
    ]);
    setPlans(plansRes.results);
    setSubscription(subscriptionRes ?? null);
    setUsage(usageRes);
    setLoading(false);
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time fetch on mount
    loadAll();
  }, []);

  function choosePlan(code: string) {
    setMessage(null);
    setError(null);
    setSelectedPlan((prev) => (prev === code ? null : code));
  }

  async function handleSubscribe(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPlan) return;
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      const res = await apiFetch<{ instructions: string }>("/api/v1/billing/subscribe/", {
        method: "POST",
        body: JSON.stringify({ plan_code: selectedPlan, phone, method }),
      });
      setMessage(res.instructions || "Payment initiated. Follow the prompt on your phone.");
      setSelectedPlan(null);
      setPhone("");
      await loadAll();
    } catch {
      setError("Could not start payment. Check the mobile money number and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel() {
    setCancelling(true);
    try {
      await apiFetch("/api/v1/billing/cancel/", { method: "POST" });
      await loadAll();
    } finally {
      setCancelling(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl space-y-6">
        <div className="h-6 w-40 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="h-24 animate-pulse rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-48 animate-pulse rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
          <Wallet size={19} />
        </span>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">Billing &amp; Plans</h1>
      </div>

      {message && (
        <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">
          {message}
        </p>
      )}
      {error && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </p>
      )}

      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
        <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
          <CreditCard size={14} />
          Current plan
        </h2>
        {subscription ? (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-gray-50">
                {subscription.plan.name}{" "}
                <span className="capitalize text-gray-500 dark:text-gray-400">
                  ({subscription.status})
                </span>
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Renews {new Date(subscription.current_period_end).toLocaleDateString()}
              </p>
            </div>
            {subscription.auto_renew && (
              <button
                onClick={handleCancel}
                disabled={cancelling}
                className="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-60 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-900/20"
              >
                {cancelling ? "Cancelling..." : "Cancel auto-renew"}
              </button>
            )}
          </div>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            You&apos;re on the Free plan. Choose a plan below to unlock unlimited downloads, more
            AI Tutor questions and advanced analytics.
          </p>
        )}
      </div>

      {usage.length > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
            <Activity size={14} />
            Usage today
          </h2>
          <ul className="divide-y divide-gray-100 text-sm dark:divide-gray-800">
            {usage.map((u) => (
              <li key={u.feature_key} className="flex justify-between py-1.5">
                <span className="capitalize text-gray-600 dark:text-gray-300">
                  {u.feature_key.replace(/_/g, " ")}
                </span>
                <span className="font-medium text-gray-900 dark:text-gray-100">{u.count}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {plans.map((plan) => {
          const isCurrent = subscription?.plan.code === plan.code;
          const isSelected = selectedPlan === plan.code;
          return (
            <div
              key={plan.id}
              className={`flex flex-col gap-3 rounded-lg border bg-white p-4 shadow-sm dark:bg-gray-900 ${
                isSelected
                  ? "border-brand-400 ring-1 ring-brand-400"
                  : "border-gray-200 dark:border-gray-800"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-gray-900 dark:text-gray-50">
                    {plan.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    ${plan.price} / {plan.billing_period}
                  </p>
                </div>
                {isCurrent && (
                  <span className="shrink-0 rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-medium text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
                    Current
                  </span>
                )}
              </div>

              {plan.features?.length > 0 && (
                <ul className="space-y-1 text-xs text-gray-600 dark:text-gray-300">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-1.5">
                      <Check size={12} className="shrink-0 text-brand-500" />
                      <span className="capitalize">{f.replace(/_/g, " ")}</span>
                    </li>
                  ))}
                </ul>
              )}

              <button
                onClick={() => choosePlan(plan.code)}
                disabled={isCurrent}
                className={`mt-auto rounded-md px-3 py-1.5 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50 ${
                  isSelected
                    ? "bg-brand-700 text-white"
                    : "bg-brand-600 text-white hover:bg-brand-700"
                }`}
              >
                {isCurrent ? "Active" : isSelected ? "Selected" : "Choose plan"}
              </button>
            </div>
          );
        })}
      </div>

      {selectedPlan && (
        <form
          onSubmit={handleSubscribe}
          className="space-y-4 rounded-lg border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-gray-900"
        >
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-50">
            Pay for {plans.find((p) => p.code === selectedPlan)?.name}
          </h2>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Mobile money number
            </label>
            <input
              type="text"
              required
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="07XXXXXXXX"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Method</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value as "ecocash" | "onemoney")}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            >
              <option value="ecocash">EcoCash</option>
              <option value="onemoney">OneMoney</option>
            </select>
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={submitting}
              className="flex-1 rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {submitting ? "Submitting..." : "Subscribe"}
            </button>
            <button
              type="button"
              onClick={() => setSelectedPlan(null)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
