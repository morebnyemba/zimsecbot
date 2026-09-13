"use client";

import { useCallback, useEffect, useState } from "react";
import { BookOpen, Check, Plus } from "lucide-react";

import { apiFetch, type Paginated } from "@/lib/api";
import { subjectColor } from "@/lib/subject-colors";
import type { StudentSubject, Subject } from "@/lib/types";

export default function SubjectsPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [mySubjects, setMySubjects] = useState<StudentSubject[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    const [subjectsRes, mineRes] = await Promise.all([
      apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true"),
      apiFetch<Paginated<StudentSubject>>("/api/v1/profile/me/subjects/"),
    ]);
    setSubjects(subjectsRes.results);
    setMySubjects(mineRes.results);
    setLoading(false);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time fetch on mount
    loadData();
  }, [loadData]);

  const mySubjectIds = new Set(mySubjects.map((s) => s.subject.id));

  async function addSubject(subjectId: string) {
    setBusyId(subjectId);
    try {
      await apiFetch("/api/v1/profile/me/subjects/", {
        method: "POST",
        body: JSON.stringify({ subject_id: subjectId }),
      });
      await loadData();
    } finally {
      setBusyId(null);
    }
  }

  async function removeSubject(subjectId: string) {
    setBusyId(subjectId);
    try {
      await apiFetch(`/api/v1/profile/me/subjects/${subjectId}/`, { method: "DELETE" });
      await loadData();
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-32 animate-pulse rounded bg-gray-100 dark:bg-gray-800" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-28 animate-pulse rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">Subjects</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Pick the subjects you&apos;re revising. They&apos;ll show up on your dashboard and quiz generator.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {subjects.map((subject) => {
          const selected = mySubjectIds.has(subject.id);
          const color = subjectColor(subject.code || subject.id);
          return (
            <div
              key={subject.id}
              className="flex flex-col justify-between gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900"
            >
              <div className="flex items-start gap-3">
                <span
                  className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${color.bg} ${color.text}`}
                >
                  <BookOpen size={17} />
                </span>
                <div className="min-w-0">
                  <p className="font-medium text-gray-900 dark:text-gray-50">{subject.name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {subject.code} · {subject.level} · {subject.tier}
                  </p>
                </div>
              </div>
              <button
                onClick={() => (selected ? removeSubject(subject.id) : addSubject(subject.id))}
                disabled={busyId === subject.id}
                className={
                  selected
                    ? "flex items-center justify-center gap-1.5 rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                    : "flex items-center justify-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-60"
                }
              >
                {selected ? <Check size={15} /> : <Plus size={15} />}
                {selected ? "Added · Remove" : "Add to my subjects"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
