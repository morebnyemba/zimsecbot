"use client";

import { CrudPage } from "@/components/CrudPage";
import type { ColumnConfig, FieldConfig, RecordWithId } from "@/lib/crud-types";

interface Note extends RecordWithId {
  title: string;
  subject: string;
  topic: string | null;
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
];

const columns: ColumnConfig<Note>[] = [
  { key: "title", label: "Title" },
  { key: "subject", label: "Subject" },
  { key: "topic", label: "Topic" },
];

export default function NotesPage() {
  return (
    <CrudPage<Note> title="Notes" endpoint="/api/v1/notes/" fields={fields} columns={columns} />
  );
}
