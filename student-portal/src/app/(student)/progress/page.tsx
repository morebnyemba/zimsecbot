"use client";

import { useEffect, useState } from "react";
import { Flame, Lightbulb, ListChecks, Trophy } from "lucide-react";

import { apiFetch, type Paginated } from "@/lib/api";
import { accuracyStatus, relativeTime } from "@/lib/format";
import type { QuizAttempt, StudentAnalytics } from "@/lib/types";

export default function ProgressPage() {
  const [attempts, setAttempts] = useState<QuizAttempt[]>([]);
  const [analytics, setAnalytics] = useState<StudentAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const [attemptsRes, analyticsRes] = await Promise.all([
        apiFetch<Paginated<QuizAttempt>>("/api/v1/quizzes/attempts/"),
        apiFetch<StudentAnalytics>("/api/v1/analytics/me/"),
      ]);
      setAttempts(attemptsRes.results);
      setAnalytics(analyticsRes);
      setLoading(false);
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-24 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="h-24 animate-pulse rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">Progress</h1>

      {analytics?.streak && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
              <Flame size={18} />
            </span>
            <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">Current streak</p>
            <p className="mt-0.5 text-2xl font-semibold text-gray-900 dark:text-gray-50">
              {analytics.streak.current_streak} <span className="text-sm font-normal text-gray-400">days</span>
            </p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-violet-50 text-violet-600 dark:bg-violet-900/30 dark:text-violet-400">
              <Trophy size={18} />
            </span>
            <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">Longest streak</p>
            <p className="mt-0.5 text-2xl font-semibold text-gray-900 dark:text-gray-50">
              {analytics.streak.longest_streak} <span className="text-sm font-normal text-gray-400">days</span>
            </p>
          </div>
        </div>
      )}

      {analytics && analytics.topic_performance.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
            Topic Performance
          </h2>
          <div className="divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white dark:divide-gray-800 dark:border-gray-800 dark:bg-gray-900">
            {analytics.topic_performance.map((tp) => {
              const pct = Math.round(tp.accuracy);
              const status = accuracyStatus(pct);
              return (
                <div key={tp.id} className="px-4 py-3">
                  <div className="flex items-center justify-between text-sm">
                    <p className="text-gray-700 dark:text-gray-300">
                      <span className="font-medium text-gray-900 dark:text-gray-50">{tp.subject_name}</span>{" "}
                      · {tp.topic_name}
                    </p>
                    <p className={`font-semibold ${status.text}`}>{pct}%</p>
                  </div>
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
                      <div className={`h-full rounded-full ${status.bar}`} style={{ width: `${pct}%` }} />
                    </div>
                    <span className="shrink-0 text-xs text-gray-400">{tp.attempts_count} attempts</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {analytics && analytics.recommendations.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
            Recommendations
          </h2>
          <div className="space-y-2">
            {analytics.recommendations.map((rec) => (
              <div
                key={rec.id}
                className="flex gap-3 rounded-lg border border-brand-100 bg-brand-50 p-3 text-sm text-brand-900 dark:border-brand-900 dark:bg-brand-900/20 dark:text-brand-200"
              >
                <Lightbulb size={16} className="mt-0.5 shrink-0 text-brand-500 dark:text-brand-400" />
                <div>
                  <p className="font-medium">
                    {rec.subject_name} · {rec.topic_name}
                  </p>
                  <p className="text-brand-800/90 dark:text-brand-300">{rec.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Quiz Attempts
        </h2>
        {attempts.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-lg border border-gray-200 bg-white p-10 text-center dark:border-gray-800 dark:bg-gray-900">
            <ListChecks size={26} className="text-gray-300 dark:text-gray-600" />
            <p className="text-sm text-gray-400">No quiz attempts yet. Take a quiz to see your progress.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 overflow-hidden rounded-lg border border-gray-200 bg-white dark:divide-gray-800 dark:border-gray-800 dark:bg-gray-900">
            {attempts.map((attempt) => {
              const total = attempt.total_marks || 1;
              const pct = Math.round((attempt.marks_awarded / total) * 100);
              const status = accuracyStatus(pct);
              return (
                <div key={attempt.id} className="flex items-center gap-4 px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {relativeTime(attempt.started_at)}
                    </p>
                    <span
                      className={
                        attempt.completed_at
                          ? "mt-1 inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
                          : "mt-1 inline-block rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400"
                      }
                    >
                      {attempt.completed_at ? "Completed" : "In progress"}
                    </span>
                  </div>
                  <p className={`shrink-0 text-sm font-semibold ${status.text}`}>
                    {attempt.marks_awarded}/{attempt.total_marks}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
