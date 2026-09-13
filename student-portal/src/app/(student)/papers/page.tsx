"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";

import { apiFetch, isFeatureLockedError, type Paginated } from "@/lib/api";
import type { PastPaper, Subject } from "@/lib/types";

export default function PapersPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [papers, setPapers] = useState<PastPaper[]>([]);
  const [subjectFilter, setSubjectFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [upgradePrompt, setUpgradePrompt] = useState<{ message: string; upgradeUrl: string } | null>(
    null,
  );

  const loadPapers = useCallback(async (subjectId: string) => {
    setLoading(true);
    const query = subjectId ? `?subject=${subjectId}` : "";
    const res = await apiFetch<Paginated<PastPaper>>(`/api/v1/papers/${query}`);
    setPapers(res.results);
    setLoading(false);
  }, []);

  useEffect(() => {
    async function loadSubjects() {
      const res = await apiFetch<Paginated<Subject>>("/api/v1/subjects/?is_active=true");
      setSubjects(res.results);
    }

    loadSubjects();
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time fetch on mount
    loadPapers("");
  }, [loadPapers]);

  async function handleDownload(paper: PastPaper) {
    try {
      const data = await apiFetch<{ file_url: string }>(`/api/v1/papers/${paper.id}/download/`);
      window.open(data.file_url, "_blank");
    } catch (err) {
      if (isFeatureLockedError(err)) {
        setUpgradePrompt({
          message: err.body.error.message,
          upgradeUrl: err.body.error.upgrade_url,
        });
        return;
      }
      throw err;
    }
  }

  return (
    <div className="space-y-6">
      {upgradePrompt && (
        <div className="flex items-center justify-between rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-300">
          <span>{upgradePrompt.message}</span>
          <a
            href={upgradePrompt.upgradeUrl}
            className="ml-4 shrink-0 rounded-md bg-amber-600 px-3 py-1.5 font-medium text-white hover:bg-amber-700"
          >
            Upgrade plan
          </a>
        </div>
      )}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-50">Past Papers</h1>
        <select
          value={subjectFilter}
          onChange={(e) => {
            setSubjectFilter(e.target.value);
            loadPapers(e.target.value);
          }}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
        >
          <option value="">All subjects</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg bg-gray-100 dark:bg-gray-800" />
          ))}
        </div>
      ) : papers.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-gray-200 bg-white p-10 text-center dark:border-gray-800 dark:bg-gray-900">
          <FileText size={26} className="text-gray-300 dark:text-gray-600" />
          <p className="text-sm text-gray-400">No past papers found.</p>
        </div>
      ) : (
        <>
          {/* Card list on small screens; a table doesn't fit comfortably on a phone. */}
          <div className="grid grid-cols-1 gap-3 sm:hidden">
            {papers.map((paper) => (
              <div
                key={paper.id}
                className="flex items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-800 dark:bg-gray-900"
              >
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400">
                  <FileText size={16} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-gray-900 dark:text-gray-50">
                    {paper.subject_name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {paper.year} · {paper.session} · Paper {paper.paper_number} · {paper.paper_type}
                  </p>
                </div>
                <button
                  onClick={() => handleDownload(paper)}
                  aria-label="Download"
                  className="shrink-0 rounded-md border border-gray-300 p-2 text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                >
                  <Download size={15} />
                </button>
              </div>
            ))}
          </div>

          <div className="hidden overflow-hidden rounded-lg border border-gray-200 bg-white sm:block dark:border-gray-800 dark:bg-gray-900">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-gray-500 dark:bg-gray-800/60 dark:text-gray-400">
                <tr>
                  <th className="px-4 py-2">Subject</th>
                  <th className="px-4 py-2">Year</th>
                  <th className="px-4 py-2">Session</th>
                  <th className="px-4 py-2">Paper</th>
                  <th className="px-4 py-2">Type</th>
                  <th className="px-4 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {papers.map((paper) => (
                  <tr key={paper.id} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="px-4 py-2 text-gray-900 dark:text-gray-100">{paper.subject_name}</td>
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-400">{paper.year}</td>
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-400">{paper.session}</td>
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-400">{paper.paper_number}</td>
                    <td className="px-4 py-2 text-gray-600 dark:text-gray-400">{paper.paper_type}</td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={() => handleDownload(paper)}
                        className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                      >
                        <Download size={13} />
                        Download
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
