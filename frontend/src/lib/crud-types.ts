import type { ReactNode } from "react";

export type FieldType = "text" | "number" | "textarea" | "checkbox" | "select" | "file" | "json";

export interface FieldOption {
  value: string;
  label: string;
}

export interface FieldConfig {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  /** Static choices, for enum-style fields. */
  options?: FieldOption[];
  /** API endpoint to fetch dynamic choices from, for FK fields (e.g. "/api/v1/subjects/"). */
  optionsEndpoint?: string;
  /** Extracts the display label from a fetched option record. */
  optionLabel?: (item: Record<string, unknown>) => string;
  /** Allows clearing an optional FK field. */
  allowEmpty?: boolean;
}

export interface ColumnConfig<T> {
  key: string;
  label: string;
  render?: (item: T) => ReactNode;
}

export interface RecordWithId {
  id: string;
  [key: string]: unknown;
}
