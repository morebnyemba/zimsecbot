"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiFetch, type Paginated } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { QuizAttempt, StudentSubject } from "@/lib/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [mySubjects, setMySubjects] = useState<StudentSubject[]>([]);
  const [recentAttempts, setRecentAttempts] = useState<QuizAttempt[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const [subjectsRes, attemptsRes] = await Promise.all([
        apiFetch<Paginated<StudentSubject>>("/api/v1/profile/me/subjects/"),
        apiFetch<Paginated<QuizAttempt>>("/api/v1/quizzes/attempts/"),
      ]);
      setMySubjects(subjectsRes.results);
      setRecentAttempts(attemptsRes.results.slice(0, 5));
      setLoading(false);
    }

    loadData();
  }, []);

  if (loading) return <p className="text-gray-400">Loading…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Welcome back, {user?.first_name || user?.email}</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Link
          href="/subjects"
          className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:border-blue-300"
        >
          <p className="text-sm text-gray-500">My subjects</p>
          <p className="mt-1 text-2xl font-semibold">{mySubjects.length}</p>
        </Link>
        <Link
          href="/quiz"
          className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:border-blue-300"
        >
          <p className="text-sm text-gray-500">Take a quiz</p>
          <p className="mt-1 text-sm font-medium text-blue-600">Generate a new quiz →</p>
        </Link>
        <Link
          href="/progress"
          className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:border-blue-300"
        >
          <p className="text-sm text-gray-500">Quiz attempts</p>
          <p className="mt-1 text-2xl font-semibold">{recentAttempts.length}</p>
        </Link>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
          My Subjects
        </h2>
        {mySubjects.length === 0 ? (
          <p className="text-gray-400">
            You haven&apos;t added any subjects yet.{" "}
            <Link href="/subjects" className="font-medium text-blue-600 hover:underline">
              Choose your subjects
            </Link>
            .
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {mySubjects.map((s) => (
              <span
                key={s.id}
                className="rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700"
              >
                {s.subject.name}
              </span>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Recent Quiz Attempts
        </h2>
        {recentAttempts.length === 0 ? (
          <p className="text-gray-400">No quiz attempts yet.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-gray-500">
                <tr>
                  <th className="px-4 py-2">Started</th>
                  <th className="px-4 py-2">Score</th>
                </tr>
              </thead>
              <tbody>
                {recentAttempts.map((attempt) => (
                  <tr key={attempt.id} className="border-t border-gray-100">
                    <td className="px-4 py-2">
                      {new Date(attempt.started_at).toLocaleString()}
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
