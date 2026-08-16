export type Subject = {
  id: string;
  name: string;
  code: string;
  level: string;
  tier: string;
  is_active: boolean;
};

export type StudentSubject = {
  id: string;
  subject: Subject;
  subject_id?: string;
};

export type PastPaper = {
  id: string;
  subject: string;
  subject_name: string;
  year: number;
  session: string;
  paper_number: number;
  paper_type: string;
  file: string;
  marking_scheme: string | null;
  marking_scheme_detail: { id: string; file: string } | null;
};

export type Note = {
  id: string;
  subject: string;
  topic: string | null;
  subtopic: string | null;
  title: string;
  content: string;
  media: string | null;
};

export type QuizQuestion = {
  id: string;
  question_text: string;
  question_type: "mcq" | "structured" | "essay" | "practical";
  options: string[];
  marks: number;
};

export type Quiz = {
  id: string;
  subject: string;
  topic: string | null;
  difficulty: string;
  source_channel: string;
  created_at: string;
  quiz_questions: QuizQuestion[];
};

export type QuizAnswerResult = {
  question_id: string;
  is_correct: boolean;
  marks_awarded: number;
  explanation: string;
};

export type QuizAttempt = {
  id: string;
  quiz: string;
  score: number | null;
  total_marks: number;
  marks_awarded: number;
  started_at: string;
  completed_at: string | null;
  answers: QuizAnswerResult[];
};

export type StudentProfile = {
  email: string;
  level: string;
  exam_year: number | null;
  school_name: string;
  preferences: Record<string, unknown>;
};

export type AIMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: unknown[];
  created_at: string;
};

export type AskResponse = {
  session_id: string;
  answer: string;
  sources: unknown[];
};

export type TopicPerformance = {
  id: string;
  subject_name: string;
  topic_name: string;
  attempts_count: number;
  correct_count: number;
  accuracy: number;
};

export type StudyStreak = {
  current_streak: number;
  longest_streak: number;
  last_activity_date: string | null;
};

export type Recommendation = {
  id: string;
  subject_name: string;
  topic_name: string;
  reason: string;
  message: string;
  created_at: string;
};

export type StudentAnalytics = {
  topic_performance: TopicPerformance[];
  recommendations: Recommendation[];
  streak: StudyStreak | null;
  recent_scores: (number | null)[];
};
