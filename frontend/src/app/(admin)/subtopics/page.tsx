"use client";

import { CrudPage } from "@/components/CrudPage";
import type { ColumnConfig, FieldConfig, RecordWithId } from "@/lib/crud-types";

interface Subtopic extends RecordWithId {
  topic: string;
  name: string;
  order: number;
}

const fields: FieldConfig[] = [
  {
    name: "topic",
    label: "Topic",
    type: "select",
    required: true,
    optionsEndpoint: "/api/v1/topics/",
    optionLabel: (t) => String(t.name),
  },
  { name: "name", label: "Name", type: "text", required: true },
  { name: "order", label: "Order", type: "number" },
];

const columns: ColumnConfig<Subtopic>[] = [
  { key: "topic", label: "Topic" },
  { key: "name", label: "Name" },
  { key: "order", label: "Order" },
];

export default function SubtopicsPage() {
  return (
    <CrudPage<Subtopic>
      title="Subtopics"
      endpoint="/api/v1/subtopics/"
      fields={fields}
      columns={columns}
    />
  );
}
