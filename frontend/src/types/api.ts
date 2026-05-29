// --- Roadmap List (GET /roadmaps) ---

export interface RoadmapListItem {
  roadmap_id: string;
  topic: string;
  overall_score: number;
}

export interface RoadmapListResponse {
  items: RoadmapListItem[];
  total_count: number;
}

// --- Roadmap Detail (GET /roadmaps/:id) ---

export interface RoadmapTreeNode {
  id: string;
  title: string;
  description: string;
  level: "major" | "middle" | "detail";
  score: number;
  order: number;
  children: RoadmapTreeNode[];
  last_quiz_at: string | null;
}

export interface RoadmapTree {
  roadmap_id: string;
  topic: string;
  overall_score: number;
  items: RoadmapTreeNode[];
}

// --- Topic Candidates ---

export type TopicSource = "preset" | "note" | "manual";

export interface TopicCandidate {
  name: string;
  source: TopicSource;
  note_count: number;
}

export interface TopicCandidatesResponse {
  candidates: TopicCandidate[];
}

// --- Roadmap Generation ---

export type JobStatus = "queued" | "running" | "completed" | "failed";

export interface GenerateResponse {
  job_id: string;
  status: "queued";
}

export type GenerationJobResponse =
  | { status: "queued" }
  | { status: "running" }
  | { status: "completed"; roadmap_id: string }
  | { status: "failed"; error_code: string; error_message: string };

// --- Session (POST /sessions) ---

export interface StartSessionResponse {
  session_id: string;
  resume_required: boolean;
  resume_session_id: string | null;
}

// --- Item CRUD ---

export interface RoadmapItemDTO {
  id: string;
  roadmap_id: string;
  parent_id: string | null;
  title: string;
  description: string;
  level: "major" | "middle" | "detail";
  order: number;
  score: number;
}

export interface AddItemResponse {
  created_item: RoadmapItemDTO;
}

export interface MoveItemResponse {
  moved_item: RoadmapItemDTO;
}

export interface DeleteItemResponse {
  deleted_item_ids: string[];
  deleted_count: number;
}

// --- Session State (from quiz graph) ---

export interface ConfirmationPoint {
  id: string;
  content: string;
  format: "knowledge" | "knowledge_and_practice";
}

export interface QuizAnswerRecord {
  question_number: number;
  confirmation_point_id: string;
  question_text: string;
  answer_type: "textarea" | "code";
  answer_text: string;
  score: number;
  feedback: string;
}

/**
 * SessionState — backend の TypedDict(total=False) に合わせ、
 * グラフ実行後に段階的に埋まるフィールドはオプショナル。
 * 基本フィールド（session_id 等）は常に存在する。
 */
export interface SessionState {
  session_id: string;
  roadmap_item_id: string;
  roadmap_item_level: "detail" | "middle" | "major";
  roadmap_item_title: string;
  roadmap_item_description: string;
  is_resumed: boolean;
  topic_overview?: string;
  confirmation_points?: ConfirmationPoint[];
  current_point_index?: number;
  current_question_text?: string;
  current_answer_type?: "textarea" | "code";
  user_input?: string;
  input_source?: "form" | "chat";
  input_type?: "answer" | "question" | "explanation_request";
  next_action?: "next" | "deepdive" | "complete";
  answers?: QuizAnswerRecord[];
  total_questions_asked?: number;
  /** 解説生成ノードが返す解説テキスト */
  explanation_text?: string;
  /** チャット応答ノードが返すテキスト */
  chat_response_text?: string;
}

// --- Competitive Quiz (GET/POST /algorithm-quiz/*) ---

export interface AlgoTheme {
  id: string;
  category: string;
  label: string;
}

export interface ThemesResponse {
  themes: AlgoTheme[];
}

export interface ProblemExample {
  input: string;
  output: string;
}

export interface CompetitiveStartResponse {
  session_id: string;
  theme_id: string;
  theme_label: string;
  theme_category: string;
  programming_language: "python" | "typescript";
  problem_statement: string;
  input_format: string;
  output_format: string;
  constraints: string;
  examples: ProblemExample[];
}

export interface CompetitiveAnswerResponse {
  session_id: string;
  score: number;
  feedback: string;
  time_complexity: string;
  space_complexity: string;
  improvement_suggestions: string;
  rubric_scores_json: string;
}

export interface CompetitiveSessionResponse {
  session_id: string;
  theme_id: string;
  theme_label: string;
  theme_category: string;
  programming_language: string;
  problem_statement: string;
  input_format: string;
  output_format: string;
  constraints: string;
  examples: ProblemExample[];
  status: "in_progress" | "completed";
  created_at: string;
  score?: number;
  feedback?: string;
  time_complexity?: string;
  space_complexity?: string;
  improvement_suggestions?: string;
  rubric_scores_json?: string;
}

export interface CompetitiveSessionListItem {
  session_id: string;
  theme_id: string;
  theme_label: string;
  theme_category: string;
  programming_language: string;
  status: "in_progress" | "completed";
  score?: number;
}

export interface CompetitiveSessionListResponse {
  sessions: CompetitiveSessionListItem[];
}

// --- Feedback (GET /ingestion/feedbacks) ---

export interface FeedbackListItem {
  id: string;
  source_path: string;
  roadmap_item_id: string | null;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}

export interface FeedbackListResponse {
  items: FeedbackListItem[];
  total_count: number;
}

// --- Session Detail (GET /sessions/:id) ---

export interface SessionDetailResponse {
  session_id: string;
  session: {
    id: string;
    roadmap_item_id: string;
    status: "in_progress" | "completed";
    completed_at: string | null;
  };
  graph_state?: SessionState;
}
