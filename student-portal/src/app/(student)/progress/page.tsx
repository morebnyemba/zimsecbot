"use client";

import { useEffect, useState } from "react";

import { apiFetch, type Paginated } from "@/lib/api";
import type { QuizAttempt } from "@/lib/types";

export default function ProgressPage() {
  const [attempts, setAttempts] = useState<QuizAttempt[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAttempts() {
      const res = await apiFetch<Paginated<QuizAttempt>>("/api/v1/quizzes/attempts/");
      setAttempts(res.results);
      setLoading(false);
    }

    loadAttempts();
  }, []);

  if (loading) return <p className="text-gray-400">Loading…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Progress</h1>

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
  );
}
