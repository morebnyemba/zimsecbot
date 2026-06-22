"use client";

import { CrudPage } from "@/components/CrudPage";
import type { ColumnConfig, FieldConfig, RecordWithId } from "@/lib/crud-types";

interface PastPaper extends RecordWithId {
  subject_name: string;
  year: number;
  session: string;
  paper_number: number;
  paper_type: string;
  file: string;
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
  { name: "year", label: "Year", type: "number", required: true },
  {
    name: "session",
    label: "Session",
    type: "select",
    required: true,
    options: [
      { value: "june", label: "June" },
      { value: "november", label: "November" },
    ],
  },
  { name: "paper_number", label: "Paper Number", type: "number", required: true },
  {
    name: "paper_type",
    label: "Paper Type",
    type: "select",
    required: true,
    options: [
      { value: "multiple_choice", label: "Multiple Choice" },
      { value: "structured", label: "Structured" },
      { value: "practical", label: "Practical" },
    ],
  },
  { name: "file", label: "Paper File", type: "file", required: true },
  {
    name: "marking_scheme",
    label: "Marking Scheme",
    type: "select",
    allowEmpty: true,
    optionsEndpoint: "/api/v1/marking-schemes/",
    optionLabel: (m) => String(m.id),
  },
];

const columns: ColumnConfig<PastPaper>[] = [
  { key: "subject_name", label: "Subject" },
  { key: "year", label: "Year" },
  { key: "session", label: "Session" },
  { key: "paper_number", label: "Paper #" },
  { key: "paper_type", label: "Type" },
  {
    key: "file",
    label: "File",
    render: (p) => (
      <a href={p.file} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
        Download
      </a>
    ),
  },
];

export default function PapersPage() {
  return (
    <CrudPage<PastPaper>
      title="Past Papers"
      endpoint="/api/v1/papers/"
      fields={fields}
      columns={columns}
    />
  );
}
