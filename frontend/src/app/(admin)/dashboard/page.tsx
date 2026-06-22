"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";

interface PlatformAnalytics {
  total_students: number;
  total_subjects: number;
  total_papers: number;
  total_notes: number;
  total_questions: number;
  total_quizzes: number;
  total_quiz_attempts: number;
}

const CARD_LABELS: { key: keyof PlatformAnalytics; label: string }[] = [
  { key: "total_students", label: "Students" },
  { key: "total_subjects", label: "Active Subjects" },
  { key: "total_papers", label: "Past Papers" },
  { key: "total_notes", label: "Notes" },
  { key: "total_questions", label: "Questions" },
  { key: "total_quizzes", label: "Quizzes" },
  { key: "total_quiz_attempts", label: "Quiz Attempts" },
];

export default function DashboardPage() {
  const [data, setData] = useState<PlatformAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<PlatformAnalytics>("/api/v1/admin/analytics/platform/")
      .then(setData)
      .catch(() => setError("Failed to load analytics."));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Platform Analytics</h1>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {!data && !error && <p className="text-sm text-gray-400">Loading…</p>}
      {data && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {CARD_LABELS.map((card) => (
            <div
              key={card.key}
              className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
            >
              <p className="text-sm text-gray-500">{card.label}</p>
              <p className="mt-1 text-2xl font-semibold">{data[card.key]}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
