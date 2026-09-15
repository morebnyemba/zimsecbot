"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CreditCard, Save, User } from "lucide-react";

import { apiFetch } from "@/lib/api";
import type { StudentProfile, Subscription } from "@/lib/types";

export default function ProfilePage() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      const [profileRes, subscriptionRes] = await Promise.all([
        apiFetch<StudentProfile>("/api/v1/profile/me/"),
        apiFetch<Subscription | undefined>("/api/v1/billing/subscription/"),
      ]);
      setProfile(profileRes);
      setSubscription(subscriptionRes ?? null);
      setLoading(false);
    }

    loadProfile();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!profile) return;
    setSaving(true);
    setSaved(false);
    try {
      const updated = await apiFetch<StudentProfile>("/api/v1/profile/me/", {
        method: "PATCH",
        body: JSON.stringify({
          level: profile.level,
          exam_year: profile.exam_year,
          school_name: profile.school_name,
        }),
      });
      setProfile(updated);
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  if (loading || !profile) {
    return (
      <div className="max-w-lg space-y-4">
        <div className="h-6 w-32 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="h-64 animate-pulse rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900" />
      </div>
    );
  }

  return (
    <div className="max-w-lg space-y-6">
      <div className="flex items-center gap-3">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-100 text-lg font-semibold text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
          {profile.email.slice(0, 2).toUpperCase()}
        </span>
        <div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">My Profile</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">{profile.email}</p>
        </div>
      </div>

      <Link
        href="/billing"
        className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-colors hover:border-brand-300 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-brand-700"
      >
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
            <CreditCard size={17} />
          </span>
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-50">
              {subscription ? subscription.plan.name : "Free plan"}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {subscription
                ? `Renews ${new Date(subscription.current_period_end).toLocaleDateString()}`
                : "Upgrade for more downloads and AI tutor questions"}
            </p>
          </div>
        </div>
        <span className="rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-300">
          {subscription ? "Manage" : "Upgrade"}
        </span>
      </Link>

      <form
        onSubmit={handleSubmit}
        className="space-y-5 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900"
      >
        {saved && (
          <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-400">
            Profile updated.
          </p>
        )}

        <div className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">Account</p>
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Email</label>
            <div className="relative">
              <User size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                value={profile.email}
                disabled
                className="w-full rounded-md border border-gray-300 bg-gray-50 py-2 pl-9 pr-3 text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400"
              />
            </div>
          </div>
        </div>

        <div className="space-y-4 border-t border-gray-100 pt-5 dark:border-gray-800">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">Study info</p>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Level</label>
            <select
              value={profile.level}
              onChange={(e) => setProfile({ ...profile, level: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            >
              <option value="">Select level</option>
              <option value="o_level">O-Level</option>
              <option value="a_level">A-Level</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Exam year</label>
            <input
              type="number"
              value={profile.exam_year ?? ""}
              onChange={(e) =>
                setProfile({ ...profile, exam_year: e.target.value ? Number(e.target.value) : null })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">School name</label>
            <input
              value={profile.school_name}
              onChange={(e) => setProfile({ ...profile, school_name: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          <Save size={15} />
          {saving ? "Saving..." : "Save changes"}
        </button>
      </form>
    </div>
  );
}
