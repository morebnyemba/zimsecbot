"use client";

import { useEffect, useState } from "react";

import { ApiError, apiFetch, type Paginated } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface AuditLog {
  id: string;
  user: string | null;
  user_email: string | null;
  action: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export default function AuditLogsPage() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [prevUrl, setPrevUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function fetchLogs(url?: string) {
    setLoading(true);
    try {
      const data = await apiFetch<Paginated<AuditLog>>(url ?? "/api/v1/admin/audit-logs/");
      setLogs(data.results);
      setNextUrl(data.next);
      setPrevUrl(data.previous);
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setError("You do not have permission to view the audit log.");
      } else {
        setError("Failed to load the audit log.");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial list load on mount
    fetchLogs();
  }, []);

  if (user && user.role !== "superadmin") {
    return <p className="text-sm text-red-600">You do not have permission to view the audit log.</p>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Audit Log</h1>

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <p className="p-6 text-sm text-gray-400">Loading…</p>
        ) : error ? (
          <p className="p-6 text-sm text-red-600">{error}</p>
        ) : logs.length === 0 ? (
          <p className="p-6 text-sm text-gray-400">No audit entries yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-3 font-medium">When</th>
                <th className="px-4 py-3 font-medium">User</th>
                <th className="px-4 py-3 font-medium">Action</th>
                <th className="px-4 py-3 font-medium">Metadata</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-gray-100 last:border-0">
                  <td className="px-4 py-3 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">{log.user_email ?? "—"}</td>
                  <td className="px-4 py-3 font-mono text-xs">{log.action}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">
                    {JSON.stringify(log.metadata)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {(nextUrl || prevUrl) && (
        <div className="flex justify-end gap-2">
          <button
            disabled={!prevUrl}
            onClick={() => prevUrl && fetchLogs(prevUrl)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40"
          >
            Previous
          </button>
          <button
            disabled={!nextUrl}
            onClick={() => nextUrl && fetchLogs(nextUrl)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
