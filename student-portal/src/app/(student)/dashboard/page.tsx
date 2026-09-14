"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, BookOpen, Flame, Lightbulb, ListChecks, Sparkles } from "lucide-react";

import { Sparkline } from "@/components/Sparkline";
import { apiFetch, type Paginated } from "@/lib/api";
import { accuracyStatus, relativeTime } from "@/lib/format";
import { subjectColor } from "@/lib/subject-colors";
import { useAuth } from "@/lib/auth-context";
import type { QuizAttempt, StudentAnalytics, StudentSubject } from "@/lib/types";

export default function DashboardPage() {
  const { user } = useAuth();
  const [mySubjects, setMySubjects] = useState<StudentSubject[]>([]);
  const [recentAttempts, setRecentAttempts] = useState<QuizAttempt[]>([]);
  const [analytics, setAnalytics] = useState<StudentAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      const [subjectsRes, attemptsRes, analyticsRes] = await Promise.all([
        apiFetch<Paginated<StudentSubject>>("/api/v1/profile/me/subjects/"),
        apiFetch<Paginated<QuizAttempt>>("/api/v1/quizzes/attempts/"),
        apiFetch<StudentAnalytics>("/api/v1/analytics/me/"),
      ]);
      setMySubjects(subjectsRes.results);
      setRecentAttempts(attemptsRes.results.slice(0, 5));
      setAnalytics(analyticsRes);
      setLoading(false);
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-56 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-24 animate-pulse rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900"
            />
          ))}
        </div>
      </div>
    );
  }

  const streak = analytics?.streak;
  const currentStreak = streak?.current_streak ?? 0;
  const topRecommendation = analytics?.recommendations[0];
  // recent_scores comes newest-first; reverse for a left-to-right (oldest -> newest) trend read.
  const scoreTrend = [...(analytics?.recent_scores ?? [])].reverse();

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">
        Welcome back, {user?.first_name || user?.email}
      </h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
            <Flame size={18} />
          </span>
          {currentStreak > 0 ? (
            <>
              <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">Study streak</p>
              <p className="mt-0.5 text-2xl font-semibold text-gray-900 dark:text-gray-50">
                {currentStreak} <span className="text-sm font-normal text-gray-400">days</span>
              </p>
              {!!streak?.longest_streak && (
                <p className="mt-1 text-xs text-gray-400">Best: {streak.longest_streak} days</p>
              )}
            </>
          ) : (
            <>
              <p className="mt-3 text-sm font-medium text-gray-700 dark:text-gray-300">
                Start your streak
              </p>
              <p className="mt-0.5 text-xs text-gray-400">Take a quiz today to get going.</p>
            </>
          )}
          {scoreTrend.length > 0 && (
            <div className="mt-3 border-t border-gray-100 pt-2 dark:border-gray-800">
              <Sparkline scores={scoreTrend} />
            </div>
          )}
        </div>

        <Link
          href="/subjects"
          className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:border-gray-800 dark:bg-gray-900"
        >
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-indigo-50 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-400">
            <BookOpen size={18} />
          </span>
          <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">My subjects</p>
          <p className="mt-0.5 text-2xl font-semibold text-gray-900 dark:text-gray-50">
            {mySubjects.length}
          </p>
        </Link>

        <Link
          href="/quiz"
          className="group flex flex-col justify-between rounded-lg bg-gradient-to-br from-brand-600 to-brand-700 p-4 text-white shadow-sm transition-shadow hover:shadow-md"
        >
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/15">
            <Sparkles size={18} />
          </span>
          <div className="mt-3">
            <p className="text-sm text-white/80">Ready to practice?</p>
            <p className="mt-0.5 flex items-center gap-1 text-base font-semibold">
              Generate a quiz
              <ArrowRight size={16} className="transition-transform group-hover:translate-x-0.5" />
            </p>
          </div>
        </Link>
      </div>

      {topRecommendation && (
        <Link
          href={`/quiz?subject=${topRecommendation.subject_id}&topic=${topRecommendation.topic_id}`}
          className="flex items-start gap-3 rounded-lg border border-brand-100 bg-brand-50 p-4 transition-colors hover:bg-brand-100/70 dark:border-brand-900 dark:bg-brand-900/20 dark:hover:bg-brand-900/30"
        >
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white text-brand-600 dark:bg-gray-900 dark:text-brand-400">
            <Lightbulb size={16} />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-brand-900 dark:text-brand-200">
              {topRecommendation.subject_name} · {topRecommendation.topic_name}
            </p>
            <p className="text-sm text-brand-800/80 dark:text-brand-300">{topRecommendation.message}</p>
          </div>
          <span className="mt-1 shrink-0 text-sm font-medium text-brand-700 dark:text-brand-300">
            Practice this →
          </span>
        </Link>
      )}

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
          My Subjects
        </h2>
        {mySubjects.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-lg border border-gray-200 bg-white p-10 text-center dark:border-gray-800 dark:bg-gray-900">
            <BookOpen size={26} className="text-gray-300 dark:text-gray-600" />
            <p className="text-sm text-gray-400">You haven&apos;t added any subjects yet.</p>
            <Link href="/subjects" className="text-sm font-medium text-brand-600 hover:underline">
              Choose your subjects
            </Link>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {mySubjects.map((s) => {
              const color = subjectColor(s.subject.code || s.subject.id);
              return (
                <span
                  key={s.id}
                  className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${color.bg} ${color.text}`}
                >
                  <span className={`h-1.5 w-1.5 rounded-full ${color.dot}`} />
                  {s.subject.name}
                </span>
              );
            })}
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Recent Quiz Attempts
        </h2>
        {recentAttempts.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-lg border border-gray-200 bg-white p-10 text-center dark:border-gray-800 dark:bg-gray-900">
            <ListChecks size={26} className="text-gray-300 dark:text-gray-600" />
            <p className="text-sm text-gray-400">No quiz attempts yet.</p>
            <Link href="/quiz" className="text-sm font-medium text-brand-600 hover:underline">
              Take your first quiz
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 overflow-hidden rounded-lg border border-gray-200 bg-white dark:divide-gray-800 dark:border-gray-800 dark:bg-gray-900">
            {recentAttempts.map((attempt) => {
              const total = attempt.total_marks || 1;
              const pct = Math.round((attempt.marks_awarded / total) * 100);
              const status = accuracyStatus(pct);
              const color = subjectColor(attempt.subject_code || attempt.subject_name);
              return (
                <div key={attempt.id} className="flex items-center gap-4 px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {attempt.subject_name && (
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${color.bg} ${color.text}`}
                        >
                          {attempt.subject_name}
                        </span>
                      )}
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {relativeTime(attempt.started_at)}
                      </p>
                    </div>
                    <div className="mt-1.5 h-1.5 w-full max-w-[10rem] overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
                      <div className={`h-full rounded-full ${status.bar}`} style={{ width: `${pct}%` }} />
                    </div>
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
