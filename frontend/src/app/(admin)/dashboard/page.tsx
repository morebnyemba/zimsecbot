"use client";

import { useEffect, useState } from "react";
import {
  Users,
  BookOpen,
  FileText,
  StickyNote,
  HelpCircle,
  ClipboardCheck,
  BarChart3,
  type LucideIcon,
} from "lucide-react";

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

const CARD_LABELS: {
  key: keyof PlatformAnalytics;
  label: string;
  icon: LucideIcon;
  tint: string;
}[] = [
  { key: "total_students", label: "Students", icon: Users, tint: "bg-brand-50 text-brand-600" },
  { key: "total_subjects", label: "Active Subjects", icon: BookOpen, tint: "bg-indigo-50 text-indigo-600" },
  { key: "total_papers", label: "Past Papers", icon: FileText, tint: "bg-amber-50 text-amber-600" },
  { key: "total_notes", label: "Notes", icon: StickyNote, tint: "bg-rose-50 text-rose-600" },
  { key: "total_questions", label: "Questions", icon: HelpCircle, tint: "bg-purple-50 text-purple-600" },
  { key: "total_quizzes", label: "Quizzes", icon: ClipboardCheck, tint: "bg-cyan-50 text-cyan-600" },
  { key: "total_quiz_attempts", label: "Quiz Attempts", icon: BarChart3, tint: "bg-emerald-50 text-emerald-600" },
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
      <div>
        <h1 className="text-xl font-semibold">Platform Analytics</h1>
        <p className="mt-1 text-sm text-gray-500">A live snapshot of activity across Zimfundi.</p>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {!data && !error && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
          {CARD_LABELS.map((card) => (
            <div
              key={card.key}
              className="animate-pulse rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
            >
              <div className="h-9 w-9 rounded-full bg-gray-100" />
              <div className="mt-3 h-3 w-16 rounded bg-gray-100" />
              <div className="mt-2 h-6 w-10 rounded bg-gray-100" />
            </div>
          ))}
        </div>
      )}

      {data && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7">
          {CARD_LABELS.map((card) => {
            const Icon = card.icon;
            return (
              <div
                key={card.key}
                className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
              >
                <span className={`inline-flex h-9 w-9 items-center justify-center rounded-full ${card.tint}`}>
                  <Icon size={18} strokeWidth={2} />
                </span>
                <p className="mt-3 text-sm text-gray-500">{card.label}</p>
                <p className="mt-0.5 text-2xl font-semibold text-gray-900">{data[card.key]}</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
