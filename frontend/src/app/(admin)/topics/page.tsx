"use client";

import { CrudPage } from "@/components/CrudPage";
import type { ColumnConfig, FieldConfig, RecordWithId } from "@/lib/crud-types";

interface Topic extends RecordWithId {
  subject: string;
  name: string;
  order: number;
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
  { name: "name", label: "Name", type: "text", required: true },
  { name: "order", label: "Order", type: "number" },
];

const columns: ColumnConfig<Topic>[] = [
  { key: "subject", label: "Subject" },
  { key: "name", label: "Name" },
  { key: "order", label: "Order" },
];

export default function TopicsPage() {
  return (
    <CrudPage<Topic> title="Topics" endpoint="/api/v1/topics/" fields={fields} columns={columns} />
  );
}
