"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { CheckCircle2, ListChecks, RotateCcw, Send, Trophy, XCircle } from "lucide-react";
import clsx from "clsx";

import { apiFetch } from "@/lib/api";
import type { Quiz, QuizAttempt } from "@/lib/types";

function scrollToQuestion(index: number) {
  document.getElementById(`question-${index}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
}

export default function QuizTakePage() {
  const params = useParams<{ id: string }>();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadQuiz() {
      const data = await apiFetch<Quiz>(`/api/v1/quizzes/${params.id}/`);
      setQuiz(data);
      setLoading(false);
    }

    loadQuiz();
  }, [params.id]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!quiz) return;
    setSubmitting(true);
    try {
      const result = await apiFetch<QuizAttempt>(`/api/v1/quizzes/${quiz.id}/attempts/`, {
        method: "POST",
        body: JSON.stringify({
          answers: quiz.quiz_questions.map((q) => ({
            question_id: q.id,
            student_answer: answers[q.id] ?? "",
          })),
        }),
      });
      setAttempt(result);
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <div className="h-6 w-24 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-20 animate-pulse rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900"
            />
          ))}
        </div>
        <div className="hidden h-48 animate-pulse rounded-lg border border-gray-200 bg-white lg:block dark:border-gray-800 dark:bg-gray-900" />
      </div>
    );
  }
  if (!quiz) return <p className="text-gray-400">Quiz not found.</p>;

  const answeredCount = Object.values(answers).filter(Boolean).length;

  if (attempt) {
    const resultByQuestion = new Map(attempt.answers.map((a) => [a.question_id, a]));
    const total = attempt.total_marks || 1;
    const pct = Math.round((attempt.marks_awarded / total) * 100);
    const correctCount = attempt.answers.filter((a) => a.is_correct).length;

    return (
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Source-first so it's on top on mobile; lg:order-2 pushes it to the right column on desktop. */}
        <div className="lg:order-2 lg:col-span-1">
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm lg:sticky lg:top-20 dark:border-gray-800 dark:bg-gray-900">
            <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
              <Trophy size={22} />
            </span>
            <h1 className="mt-3 text-lg font-semibold text-gray-900 dark:text-gray-50">Quiz results</h1>
            <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-gray-50">{pct}%</p>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              {attempt.marks_awarded}/{attempt.total_marks} marks · {correctCount}/{quiz.quiz_questions.length}{" "}
              correct
            </p>
            <div className="mt-5 flex flex-col gap-2">
              <Link
                href="/quiz"
                className="flex items-center justify-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
              >
                <RotateCcw size={14} />
                New quiz
              </Link>
              <Link
                href="/progress"
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                View progress
              </Link>
            </div>
          </div>
        </div>

        <div className="space-y-4 lg:order-1 lg:col-span-2">
          {quiz.quiz_questions.map((q, idx) => {
            const result = resultByQuestion.get(q.id);
            const correct = result?.is_correct;
            return (
              <div
                key={q.id}
                className={
                  correct
                    ? "rounded-lg border border-emerald-200 bg-emerald-50 p-4 shadow-sm dark:border-emerald-900 dark:bg-emerald-900/20"
                    : "rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm dark:border-red-900 dark:bg-red-900/20"
                }
              >
                <div className="flex items-start gap-2">
                  {correct ? (
                    <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <XCircle size={17} className="mt-0.5 shrink-0 text-red-600 dark:text-red-400" />
                  )}
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900 dark:text-gray-100">
                      {idx + 1}. {q.question_text}
                    </p>
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                      Your answer: {answers[q.id] || "—"}
                    </p>
                    <p
                      className={
                        correct
                          ? "mt-1 text-sm font-medium text-emerald-700 dark:text-emerald-400"
                          : "mt-1 text-sm font-medium text-red-700 dark:text-red-400"
                      }
                    >
                      {correct ? "Correct" : "Incorrect"} · {result?.marks_awarded}/{q.marks} marks
                    </p>
                    {result?.explanation && (
                      <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">{result.explanation}</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="space-y-4 lg:col-span-2">
        <div>
          <div className="flex items-center gap-3">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
              <ListChecks size={19} />
            </span>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">Quiz</h1>
          </div>
          <div className="mt-3 flex items-center gap-2 lg:hidden">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
              <div
                className="h-full rounded-full bg-brand-500 transition-[width]"
                style={{ width: `${(answeredCount / quiz.quiz_questions.length) * 100}%` }}
              />
            </div>
            <span className="shrink-0 text-xs text-gray-400">
              {answeredCount}/{quiz.quiz_questions.length}
            </span>
          </div>
        </div>

        {quiz.quiz_questions.map((q, idx) => (
          <div
            key={q.id}
            id={`question-${idx}`}
            className="scroll-mt-20 rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900"
          >
            <p className="font-medium text-gray-900 dark:text-gray-100">
              {idx + 1}. {q.question_text}
            </p>
            {q.question_type === "mcq" && q.options.length > 0 ? (
              <div className="mt-3 space-y-2">
                {q.options.map((option) => (
                  <label
                    key={option}
                    className="flex items-center gap-2 rounded-md border border-transparent px-2 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    <input
                      type="radio"
                      name={q.id}
                      value={option}
                      checked={answers[q.id] === option}
                      onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: option }))}
                      className="accent-brand-600"
                    />
                    {option}
                  </label>
                ))}
              </div>
            ) : (
              <textarea
                value={answers[q.id] ?? ""}
                onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                className="mt-3 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
                rows={3}
              />
            )}
          </div>
        ))}

        <button
          type="submit"
          disabled={submitting}
          className="flex w-full items-center justify-center gap-2 rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60 lg:hidden"
        >
          <Send size={15} />
          {submitting ? "Submitting..." : "Submit quiz"}
        </button>
      </div>

      <div className="hidden lg:col-span-1 lg:block">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm lg:sticky lg:top-20 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">Progress</p>
          <div className="mt-2 flex items-center gap-2">
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
              <div
                className="h-full rounded-full bg-brand-500 transition-[width]"
                style={{ width: `${(answeredCount / quiz.quiz_questions.length) * 100}%` }}
              />
            </div>
            <span className="shrink-0 text-xs text-gray-400">
              {answeredCount}/{quiz.quiz_questions.length}
            </span>
          </div>

          <div className="mt-4 grid grid-cols-5 gap-1.5">
            {quiz.quiz_questions.map((q, idx) => (
              <button
                key={q.id}
                type="button"
                onClick={() => scrollToQuestion(idx)}
                title={`Jump to question ${idx + 1}`}
                className={clsx(
                  "flex h-8 w-8 items-center justify-center rounded-md text-xs font-medium",
                  answers[q.id]
                    ? "bg-brand-600 text-white"
                    : "border border-gray-200 text-gray-500 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-800",
                )}
              >
                {idx + 1}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-md bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            <Send size={15} />
            {submitting ? "Submitting..." : "Submit quiz"}
          </button>
        </div>
      </div>
    </form>
  );
}
