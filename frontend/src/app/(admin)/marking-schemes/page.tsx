"use client";

import { CrudPage } from "@/components/CrudPage";
import type { ColumnConfig, FieldConfig, RecordWithId } from "@/lib/crud-types";

interface MarkingScheme extends RecordWithId {
  file: string;
}

const fields: FieldConfig[] = [{ name: "file", label: "File", type: "file", required: true }];

const columns: ColumnConfig<MarkingScheme>[] = [
  {
    key: "file",
    label: "File",
    render: (m) => (
      <a href={m.file} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
        {m.file.split("/").pop()}
      </a>
    ),
  },
];

export default function MarkingSchemesPage() {
  return (
    <CrudPage<MarkingScheme>
      title="Marking Schemes"
      endpoint="/api/v1/marking-schemes/"
      fields={fields}
      columns={columns}
    />
  );
}
