"use client";

import { CrudPage } from "@/components/CrudPage";
import type { ColumnConfig, FieldConfig, RecordWithId } from "@/lib/crud-types";

interface Subject extends RecordWithId {
  name: string;
  code: string;
  level: string;
  tier: number;
  is_active: boolean;
}

const fields: FieldConfig[] = [
  { name: "name", label: "Name", type: "text", required: true },
  { name: "code", label: "Code", type: "text", required: true },
  {
    name: "level",
    label: "Level",
    type: "select",
    required: true,
    options: [
      { value: "o_level", label: "O-Level" },
      { value: "a_level", label: "A-Level" },
    ],
  },
  { name: "tier", label: "Tier", type: "number", required: true },
  { name: "is_active", label: "Active", type: "checkbox" },
];

const columns: ColumnConfig<Subject>[] = [
  { key: "name", label: "Name" },
  { key: "code", label: "Code" },
  { key: "level", label: "Level" },
  { key: "tier", label: "Tier" },
  { key: "is_active", label: "Active", render: (s) => (s.is_active ? "Yes" : "No") },
];

export default function SubjectsPage() {
  return (
    <CrudPage<Subject>
      title="Subjects"
      endpoint="/api/v1/subjects/"
      fields={fields}
      columns={columns}
    />
  );
}
