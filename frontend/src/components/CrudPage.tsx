"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, apiFetch, type Paginated } from "@/lib/api";
import type { ColumnConfig, FieldConfig, RecordWithId } from "@/lib/crud-types";

type FormState = Record<string, string | boolean | File | null>;

function initialFormState(fields: FieldConfig[], item?: RecordWithId): FormState {
  const state: FormState = {};
  for (const field of fields) {
    if (field.type === "file") {
      state[field.name] = null;
    } else if (field.type === "checkbox") {
      state[field.name] = item ? Boolean(item[field.name]) : false;
    } else if (field.type === "json") {
      state[field.name] = item ? JSON.stringify(item[field.name] ?? null) : "[]";
    } else {
      const value = item?.[field.name];
      state[field.name] = value === null || value === undefined ? "" : String(value);
    }
  }
  return state;
}

function buildRequestBody(fields: FieldConfig[], form: FormState): BodyInit {
  const hasFile = fields.some((f) => f.type === "file" && form[f.name] instanceof File);

  if (hasFile) {
    const data = new FormData();
    for (const field of fields) {
      const value = form[field.name];
      if (field.type === "file") {
        if (value instanceof File) data.append(field.name, value);
        continue;
      }
      if (field.allowEmpty && value === "") continue;
      if (field.type === "json") {
        data.append(field.name, value as string);
        continue;
      }
      data.append(field.name, String(value));
    }
    return data;
  }

  const payload: Record<string, unknown> = {};
  for (const field of fields) {
    const value = form[field.name];
    if (field.type === "file") continue;
    if (field.allowEmpty && value === "") {
      payload[field.name] = null;
      continue;
    }
    if (field.type === "json") {
      try {
        payload[field.name] = JSON.parse(value as string);
      } catch {
        payload[field.name] = [];
      }
      continue;
    }
    if (field.type === "checkbox") {
      payload[field.name] = Boolean(value);
      continue;
    }
    if (field.type === "number") {
      payload[field.name] = value === "" ? null : Number(value);
      continue;
    }
    payload[field.name] = value;
  }
  return JSON.stringify(payload);
}

function formatErrors(body: unknown): string {
  if (!body || typeof body !== "object") return "Something went wrong. Please try again.";
  return Object.entries(body as Record<string, unknown>)
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(", ") : String(value)}`)
    .join(" | ");
}

interface CrudPageProps<T extends RecordWithId> {
  title: string;
  endpoint: string;
  fields: FieldConfig[];
  columns: ColumnConfig<T>[];
}

export function CrudPage<T extends RecordWithId>({
  title,
  endpoint,
  fields,
  columns,
}: CrudPageProps<T>) {
  const [items, setItems] = useState<T[]>([]);
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [prevUrl, setPrevUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [dynamicOptions, setDynamicOptions] = useState<Record<string, RecordWithId[]>>({});

  const [editingId, setEditingId] = useState<string | "new" | null>(null);
  const [form, setForm] = useState<FormState>(initialFormState(fields));
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchList = useCallback(
    async (url?: string) => {
      setLoading(true);
      setListError(null);
      try {
        const data = await apiFetch<Paginated<T>>(url ?? endpoint);
        setItems(data.results);
        setNextUrl(data.next);
        setPrevUrl(data.previous);
      } catch {
        setListError("Failed to load data.");
      } finally {
        setLoading(false);
      }
    },
    [endpoint],
  );

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial list load on mount
    fetchList();
  }, [fetchList]);

  useEffect(() => {
    const dynamicFields = fields.filter((f) => f.optionsEndpoint);
    if (dynamicFields.length === 0) return;
    (async () => {
      const entries = await Promise.all(
        dynamicFields.map(async (field) => {
          try {
            const data = await apiFetch<Paginated<RecordWithId>>(
              `${field.optionsEndpoint}?page_size=200`,
            );
            return [field.name, data.results] as const;
          } catch {
            return [field.name, []] as const;
          }
        }),
      );
      setDynamicOptions(Object.fromEntries(entries));
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function openCreateForm() {
    setForm(initialFormState(fields));
    setFormError(null);
    setEditingId("new");
  }

  function openEditForm(item: T) {
    setForm(initialFormState(fields, item));
    setFormError(null);
    setEditingId(item.id);
  }

  function closeForm() {
    setEditingId(null);
    setFormError(null);
  }

  async function handleDelete(item: T) {
    if (!window.confirm("Delete this record? This cannot be undone.")) return;
    try {
      await apiFetch(`${endpoint}${item.id}/`, { method: "DELETE" });
      fetchList();
    } catch {
      alert("Failed to delete this record.");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      const body = buildRequestBody(fields, form);
      if (editingId === "new") {
        await apiFetch(endpoint, { method: "POST", body });
      } else {
        await apiFetch(`${endpoint}${editingId}/`, { method: "PATCH", body });
      }
      closeForm();
      fetchList();
    } catch (err) {
      if (err instanceof ApiError) setFormError(formatErrors(err.body));
      else setFormError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  function renderField(field: FieldConfig) {
    const value = form[field.name];

    if (field.type === "checkbox") {
      return (
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => setForm((f) => ({ ...f, [field.name]: e.target.checked }))}
          className="h-4 w-4"
        />
      );
    }

    if (field.type === "file") {
      return (
        <input
          type="file"
          required={field.required && editingId === "new"}
          onChange={(e) =>
            setForm((f) => ({ ...f, [field.name]: e.target.files?.[0] ?? null }))
          }
          className="w-full text-sm"
        />
      );
    }

    if (field.type === "textarea" || field.type === "json") {
      return (
        <textarea
          required={field.required}
          value={(value as string) ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, [field.name]: e.target.value }))}
          rows={field.type === "json" ? 3 : 4}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      );
    }

    if (field.type === "select") {
      const options =
        field.options ??
        (dynamicOptions[field.name] ?? []).map((opt) => ({
          value: opt.id,
          label: field.optionLabel ? field.optionLabel(opt) : String(opt.id),
        }));
      return (
        <select
          required={field.required}
          value={(value as string) ?? ""}
          onChange={(e) => setForm((f) => ({ ...f, [field.name]: e.target.value }))}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        >
          {(field.allowEmpty || !field.required) && <option value="">—</option>}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      );
    }

    return (
      <input
        type={field.type === "number" ? "number" : "text"}
        required={field.required}
        value={(value as string) ?? ""}
        onChange={(e) => setForm((f) => ({ ...f, [field.name]: e.target.value }))}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{title}</h1>
        <button
          onClick={openCreateForm}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          New
        </button>
      </div>

      {editingId && (
        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
        >
          <h2 className="text-sm font-semibold text-gray-700">
            {editingId === "new" ? `New ${title}` : `Edit ${title}`}
          </h2>
          {formError && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</p>
          )}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {fields.map((field) => (
              <div key={field.name} className="space-y-1">
                <label className="text-sm font-medium text-gray-700">{field.label}</label>
                {renderField(field)}
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
            >
              {submitting ? "Saving..." : "Save"}
            </button>
            <button
              type="button"
              onClick={closeForm}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <p className="p-6 text-sm text-gray-400">Loading…</p>
        ) : listError ? (
          <p className="p-6 text-sm text-red-600">{listError}</p>
        ) : items.length === 0 ? (
          <p className="p-6 text-sm text-gray-400">No records yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                {columns.map((col) => (
                  <th key={col.key} className="px-4 py-3 font-medium">
                    {col.label}
                  </th>
                ))}
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-gray-100 last:border-0">
                  {columns.map((col) => (
                    <td key={col.key} className="px-4 py-3">
                      {col.render ? col.render(item) : String(item[col.key] ?? "")}
                    </td>
                  ))}
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => openEditForm(item)}
                      className="mr-3 text-blue-600 hover:underline"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(item)}
                      className="text-red-600 hover:underline"
                    >
                      Delete
                    </button>
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
            onClick={() => prevUrl && fetchList(prevUrl)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40"
          >
            Previous
          </button>
          <button
            disabled={!nextUrl}
            onClick={() => nextUrl && fetchList(nextUrl)}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
