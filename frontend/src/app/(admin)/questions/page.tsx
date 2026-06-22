"use client";

import { CrudPage } from "@/components/CrudPage";
import type { ColumnConfig, FieldConfig, RecordWithId } from "@/lib/crud-types";

interface Question extends RecordWithId {
  subject: string;
  question_type: string;
  difficulty: string;
  question_text: string;
  marks: number;
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
    name: "question_type",
    label: "Question Type",
    type: "select",
    required: true,
    options: [
      { value: "mcq", label: "Multiple Choice" },
      { value: "structured", label: "Structured" },
      { value: "essay", label: "Essay" },
      { value: "practical", label: "Practical" },
    ],
  },
  {
    name: "difficulty",
    label: "Difficulty",
    type: "select",
    required: true,
    options: [
      { value: "easy", label: "Easy" },
      { value: "medium", label: "Medium" },
      { value: "hard", label: "Hard" },
    ],
  },
  { name: "question_text", label: "Question Text", type: "textarea", required: true },
  { name: "options", label: "Options (JSON array)", type: "json" },
  { name: "answer", label: "Answer", type: "textarea", required: true },
  { name: "explanation", label: "Explanation", type: "textarea" },
  { name: "marks", label: "Marks", type: "number", required: true },
];

const columns: ColumnConfig<Question>[] = [
  { key: "subject", label: "Subject" },
  { key: "question_type", label: "Type" },
  { key: "difficulty", label: "Difficulty" },
  {
    key: "question_text",
    label: "Question",
    render: (q) => (
      <span>{q.question_text.length > 80 ? `${q.question_text.slice(0, 80)}…` : q.question_text}</span>
    ),
  },
  { key: "marks", label: "Marks" },
];

export default function QuestionsPage() {
  return (
    <CrudPage<Question>
      title="Questions"
      endpoint="/api/v1/questions/"
      fields={fields}
      columns={columns}
    />
  );
}
