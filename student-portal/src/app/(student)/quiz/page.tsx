"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch, type Paginated } from "@/lib/api";
import type { Quiz, Subject } from "@/lib/types";

type Topic = { id: string; subject: string; name: string; order: number };

export default function QuizGeneratePage() {
  const router = useRouter();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [topicId, setTopicId] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [questionCount, setQuestionCount] = useState(10);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSubjects() {
      const res = await apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true");
      setSubjects(res.results);
    }

    loadSubjects();
  }, []);

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
    <div className="max-w-lg space-y-6">
      <h1 className="text-xl font-semibold">Generate a quiz</h1>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
      >
        {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Subject</label>
          <select
            required
            value={subjectId}
            onChange={(e) => {
              setSubjectId(e.target.value);
              setTopicId("");
            }}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
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
          <label className="text-sm font-medium text-gray-700">Topic (optional)</label>
          <select
            value={topicId}
            onChange={(e) => setTopicId(e.target.value)}
            disabled={!subjectId}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-60"
          >
            <option value="">Any topic</option>
            {topics.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Difficulty (optional)</label>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">Any difficulty</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Number of questions</label>
          <input
            type="number"
            min={1}
            max={50}
            value={questionCount}
            onChange={(e) => setQuestionCount(Number(e.target.value))}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {submitting ? "Generating..." : "Start quiz"}
        </button>
      </form>
    </div>
  );
}
