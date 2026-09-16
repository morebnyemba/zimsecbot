"use client";

import Link from "next/link";
import { FileUp } from "lucide-react";

import { CrudPage } from "@/components/CrudPage";
import type { ColumnConfig, FieldConfig, RecordWithId } from "@/lib/crud-types";

interface Note extends RecordWithId {
  title: string;
  subject: string;
  topic: string | null;
  status: "draft" | "published";
  source: string;
}

const fields: FieldConfig[] = [
  {
    name: "subject",
    label: "Subject",
    type: "select",
    required: true,
    optionsEndpoint: "/api/v1/subjects/",
    optionLabel: (s) => `${s.name} (${s.code})`,
  },
  {
    name: "topic",
    label: "Topic",
    type: "select",
    allowEmpty: true,
    optionsEndpoint: "/api/v1/topics/",
    optionLabel: (t) => String(t.name),
  },
  {
    name: "subtopic",
    label: "Subtopic",
    type: "select",
    allowEmpty: true,
    optionsEndpoint: "/api/v1/subtopics/",
    optionLabel: (s) => String(s.name),
  },
  { name: "title", label: "Title", type: "text", required: true },
  { name: "content", label: "Content", type: "textarea", required: true },
  {
    name: "status",
    label: "Status",
    type: "select",
    required: true,
    options: [
      { value: "draft", label: "Draft" },
      { value: "published", label: "Published" },
    ],
  },
];

const columns: ColumnConfig<Note>[] = [
  { key: "title", label: "Title" },
  { key: "subject", label: "Subject" },
  { key: "topic", label: "Topic" },
  {
    key: "status",
    label: "Status",
    render: (item) => (
      <span
        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
          item.status === "published"
            ? "bg-green-50 text-green-700"
            : "bg-amber-50 text-amber-700"
        }`}
      >
        {item.status === "published" ? "Published" : "Draft"}
      </span>
    ),
  },
  { key: "source", label: "Source" },
];

export default function NotesPage() {
  return (
    <CrudPage<Note>
      title="Notes"
      endpoint="/api/v1/notes/"
      fields={fields}
      columns={columns}
      headerActions={
        <Link
          href="/notes/import"
          className="flex items-center gap-1.5 rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <FileUp size={16} />
          Import from PDF/URL
        </Link>
      }
    />
  );
}
