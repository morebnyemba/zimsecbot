"use client";

import { useEffect, useState } from "react";

import { apiFetch, type Paginated } from "@/lib/api";
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

  if (loading) return <p className="text-gray-400">Loading…</p>;

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold">Progress</h1>

      {analytics?.streak && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-500">Current streak</p>
            <p className="mt-1 text-2xl font-semibold">{analytics.streak.current_streak} days</p>
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-500">Longest streak</p>
            <p className="mt-1 text-2xl font-semibold">{analytics.streak.longest_streak} days</p>
          </div>
        </div>
      )}

      {analytics && analytics.topic_performance.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
            Topic Performance
          </h2>
          <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-gray-500">
                <tr>
                  <th className="px-4 py-2">Subject</th>
                  <th className="px-4 py-2">Topic</th>
                  <th className="px-4 py-2">Attempts</th>
                  <th className="px-4 py-2">Accuracy</th>
                </tr>
              </thead>
              <tbody>
                {analytics.topic_performance.map((tp) => (
                  <tr key={tp.id} className="border-t border-gray-100">
                    <td className="px-4 py-2">{tp.subject_name}</td>
                    <td className="px-4 py-2">{tp.topic_name}</td>
                    <td className="px-4 py-2">{tp.attempts_count}</td>
                    <td className="px-4 py-2">{tp.accuracy.toFixed(0)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
                className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-sm text-blue-800"
              >
                <p className="font-medium">
                  {rec.subject_name} · {rec.topic_name}
                </p>
                <p>{rec.message}</p>
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
          <p className="text-gray-400">No quiz attempts yet. Take a quiz to see your progress.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-gray-500">
                <tr>
                  <th className="px-4 py-2">Started</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Score</th>
                </tr>
              </thead>
              <tbody>
                {attempts.map((attempt) => (
                  <tr key={attempt.id} className="border-t border-gray-100">
                    <td className="px-4 py-2">
                      {new Date(attempt.started_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2">
                      {attempt.completed_at ? "Completed" : "In progress"}
                    </td>
                    <td className="px-4 py-2">
                      {attempt.marks_awarded} / {attempt.total_marks}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
