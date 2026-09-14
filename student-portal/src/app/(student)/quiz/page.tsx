"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { BookOpen, ListChecks, Play } from "lucide-react";

import { apiFetch, type Paginated } from "@/lib/api";
import { accuracyStatus, relativeTime } from "@/lib/format";
import { subjectColor } from "@/lib/subject-colors";
import type { Quiz, QuizAttempt, StudentSubject, Subject } from "@/lib/types";

type Topic = { id: string; subject: string; name: string; order: number };

export default function QuizGeneratePage() {
  return (
    <Suspense fallback={null}>
      <QuizGenerateForm />
    </Suspense>
  );
}

function QuizGenerateForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [mySubjects, setMySubjects] = useState<StudentSubject[]>([]);
  const [recentAttempts, setRecentAttempts] = useState<QuizAttempt[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [topicId, setTopicId] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [questionCount, setQuestionCount] = useState(10);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      const [subjectsRes, mineRes, attemptsRes] = await Promise.all([
        apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true"),
        apiFetch<Paginated<StudentSubject>>("/api/v1/profile/me/subjects/"),
        apiFetch<Paginated<QuizAttempt>>("/api/v1/quizzes/attempts/"),
      ]);
      setSubjects(subjectsRes.results);
      setMySubjects(mineRes.results);
      setRecentAttempts(attemptsRes.results.slice(0, 4));
    }

    loadData();
  }, []);

  useEffect(() => {
    // Pre-fill from a "Practice this" deep link, e.g. /quiz?subject=<id>&topic=<id>.
    const s = searchParams.get("subject");
    const t = searchParams.get("topic");
    // eslint-disable-next-line react-hooks/set-state-in-effect -- reading the initial deep-link params once
    if (s) setSubjectId(s);
    if (t) setTopicId(t);
  }, [searchParams]);

  useEffect(() => {
    async function loadTopics() {
      if (!subjectId) {
        setTopics([]);
        return;
      }
      const res = await apiFetch<Paginated<Topic>>(`/api/v1/subjects/${subjectId}/topics/`);
      setTopics(res.results);
    }

    loadTopics();
  }, [subjectId]);

  function selectSubject(id: string) {
    setSubjectId(id);
    setTopicId("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const quiz = await apiFetch<Quiz>("/api/v1/quizzes/generate/", {
        method: "POST",
        body: JSON.stringify({
          subject_id: subjectId,
          topic_id: topicId || undefined,
          difficulty: difficulty || undefined,
          question_count: questionCount,
        }),
      });
      router.push(`/quiz/${quiz.id}`);
    } catch {
      setError("Could not generate a quiz. Try a different subject or topic.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
            <ListChecks size={19} />
          </span>
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">Generate a quiz</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Practice a subject or drill one topic.</p>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900"
        >
          {error && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
              {error}
            </p>
          )}

          {mySubjects.length > 0 && (
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Quick pick</label>
              <div className="flex flex-wrap gap-2">
                {mySubjects.map((s) => {
                  const color = subjectColor(s.subject.code || s.subject.id);
                  const active = subjectId === s.subject.id;
                  return (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => selectSubject(s.subject.id)}
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors ${
                        active
                          ? `${color.bg} ${color.text} ring-1 ${color.ring}`
                          : "bg-gray-50 text-gray-500 hover:bg-gray-100 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
                      }`}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full ${color.dot}`} />
                      {s.subject.name}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Subject</label>
            <select
              required
              value={subjectId}
              onChange={(e) => selectSubject(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            >
              <option value="">Select a subject</option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Topic (optional)</label>
            <select
              value={topicId}
              onChange={(e) => setTopicId(e.target.value)}
              disabled={!subjectId}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none disabled:opacity-60 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
            >
              <option value="">Any topic</option>
              {topics.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Difficulty (optional)
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
              >
                <option value="">Any difficulty</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Number of questions
              </label>
              <input
                type="number"
                min={1}
                max={50}
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            <Play size={15} />
            {submitting ? "Generating..." : "Start quiz"}
          </button>
        </form>
      </div>

      <div className="space-y-6">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
          <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
            Your Subjects
          </p>
          {mySubjects.length === 0 ? (
            <p className="text-sm text-gray-400">
              <Link href="/subjects" className="font-medium text-brand-600 hover:underline">
                Add subjects
              </Link>{" "}
              to see them here.
            </p>
          ) : (
            <div className="space-y-1.5">
              {mySubjects.map((s) => {
                const color = subjectColor(s.subject.code || s.subject.id);
                return (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => selectSubject(s.subject.id)}
                    className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full ${color.bg} ${color.text}`}>
                      <BookOpen size={12} />
                    </span>
                    {s.subject.name}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {recentAttempts.length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900">
            <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-400">
              Recent Attempts
            </p>
            <div className="space-y-3">
              {recentAttempts.map((attempt) => {
                const total = attempt.total_marks || 1;
                const pct = Math.round((attempt.marks_awarded / total) * 100);
                const status = accuracyStatus(pct);
                return (
                  <div key={attempt.id} className="flex items-center justify-between gap-2 text-sm">
                    <div className="min-w-0">
                      <p className="truncate text-gray-700 dark:text-gray-300">{attempt.subject_name}</p>
                      <p className="text-xs text-gray-400">{relativeTime(attempt.started_at)}</p>
                    </div>
                    <span className={`shrink-0 font-semibold ${status.text}`}>{pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
