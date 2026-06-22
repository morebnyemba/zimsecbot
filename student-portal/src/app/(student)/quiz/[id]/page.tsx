"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { apiFetch } from "@/lib/api";
import type { Quiz, QuizAttempt } from "@/lib/types";

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

  if (loading) return <p className="text-gray-400">Loading…</p>;
  if (!quiz) return <p className="text-gray-400">Quiz not found.</p>;

  if (attempt) {
    const resultByQuestion = new Map(attempt.answers.map((a) => [a.question_id, a]));
    return (
      <div className="max-w-2xl space-y-6">
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h1 className="text-xl font-semibold">Quiz results</h1>
          <p className="mt-1 text-sm text-gray-500">
            Score: {attempt.marks_awarded} / {attempt.total_marks}
          </p>
        </div>
        <div className="space-y-4">
          {quiz.quiz_questions.map((q) => {
            const result = resultByQuestion.get(q.id);
            return (
              <div
                key={q.id}
                className={`rounded-lg border p-4 shadow-sm ${
                  result?.is_correct
                    ? "border-green-200 bg-green-50"
                    : "border-red-200 bg-red-50"
                }`}
              >
                <p className="font-medium">{q.question_text}</p>
                <p className="mt-1 text-sm text-gray-600">Your answer: {answers[q.id] || "—"}</p>
                <p className="mt-1 text-sm text-gray-600">
                  {result?.is_correct ? "Correct" : "Incorrect"} · {result?.marks_awarded}/
                  {q.marks} marks
                </p>
                {result?.explanation && (
                  <p className="mt-2 text-sm text-gray-700">{result.explanation}</p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold">Quiz</h1>
      {quiz.quiz_questions.map((q, idx) => (
        <div key={q.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <p className="font-medium">
            {idx + 1}. {q.question_text}
          </p>
          {q.question_type === "mcq" && q.options.length > 0 ? (
            <div className="mt-3 space-y-2">
              {q.options.map((option) => (
                <label key={option} className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name={q.id}
                    value={option}
                    checked={answers[q.id] === option}
                    onChange={() => setAnswers((prev) => ({ ...prev, [q.id]: option }))}
                  />
                  {option}
                </label>
              ))}
            </div>
          ) : (
            <textarea
              value={answers[q.id] ?? ""}
              onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
              className="mt-3 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              rows={3}
            />
          )}
        </div>
      ))}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
      >
        {submitting ? "Submitting..." : "Submit quiz"}
      </button>
    </form>
  );
}
