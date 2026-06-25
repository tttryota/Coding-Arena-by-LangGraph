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
  display_order: number;
  attempt_count: number;
  best_score: number | null;
  last_attempted_at: string | null;
}

export interface ThemesResponse {
  themes: AlgoTheme[];
}

export interface CompetitiveLanguageOption {
  id: string;
  label: string;
  editor_placeholder: string;
  enabled_order: number;
}

export interface CompetitiveLanguagesResponse {
  languages: CompetitiveLanguageOption[];
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
  programming_language: string;
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
  reference_solution: string;
}

export interface CompetitiveChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface CompetitiveQuestionResponse {
  session_id: string;
  chat_response_text: string;
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
  reference_solution?: string;
}

export interface CompetitiveSessionListItem {
  session_id: string;
  theme_id: string;
  theme_label: string;
  theme_category: string;
  programming_language: string;
  status: "in_progress" | "completed";
  created_at: string;
  score?: number;
}

export interface CompetitiveSessionListResponse {
  sessions: CompetitiveSessionListItem[];
}

// --- Algorithm Foundations (GET/POST /algorithm-foundations/*) ---

export type AlgorithmFoundationUnitKind = "foundation" | "integration";

export interface AlgorithmFoundationUnitSummary {
  unit_id: string;
  theme_id: string;
  title: string;
  display_order: number;
  prerequisite_unit_ids: string[];
  prerequisite_titles: string[];
  target_skill: string;
  unit_kind: AlgorithmFoundationUnitKind;
  problem_count: number;
  best_score: number | null;
  last_attempted_at: string | null;
  recommended: boolean;
  has_unmet_prerequisites: boolean;
}

export interface AlgorithmFoundationGroupSummary {
  group_id: string;
  group_title: string;
  order: number;
  units: AlgorithmFoundationUnitSummary[];
}

export interface AlgorithmFoundationCatalogResponse {
  total_unit_count: number;
  total_problem_count: number;
  groups: AlgorithmFoundationGroupSummary[];
}

export interface AlgorithmFoundationProblemSummary {
  problem_id: string;
  title: string;
  best_score: number | null;
  last_attempted_at: string | null;
}

export interface AlgorithmFoundationUnitDetailResponse {
  unit_id: string;
  theme_id: string;
  group_id: string;
  group_title: string;
  title: string;
  display_order: number;
  prerequisite_unit_ids: string[];
  prerequisite_titles: string[];
  allowed_knowledge: string[];
  forbidden_knowledge: string[];
  target_skill: string;
  unit_kind: AlgorithmFoundationUnitKind;
  problem_count: number;
  best_score: number | null;
  last_attempted_at: string | null;
  has_unmet_prerequisites: boolean;
  problems: AlgorithmFoundationProblemSummary[];
}

export interface AlgorithmFoundationStartResponse {
  session_id: string;
  unit_id: string;
  group_id: string;
  group_title: string;
  unit_title: string;
  target_skill: string;
  unit_kind: AlgorithmFoundationUnitKind;
  prerequisite_unit_ids: string[];
  prerequisite_titles: string[];
  allowed_knowledge: string[];
  forbidden_knowledge: string[];
  problem_id: string;
  problem_title: string;
  programming_language: string;
  problem_statement: string;
  input_format: string;
  output_format: string;
  constraints: string;
  examples: ProblemExample[];
  recommended: boolean;
  has_unmet_prerequisites: boolean;
}

export interface AlgorithmFoundationAnswerResponse {
  session_id: string;
  score: number;
  feedback: string;
  time_complexity: string;
  space_complexity: string;
  improvement_suggestions: string;
  rubric_scores_json: string;
  reference_solution: string;
}

export interface AlgorithmFoundationSessionResponse
  extends AlgorithmFoundationStartResponse {
  prerequisite_unit_ids: string[];
  prerequisite_titles: string[];
  allowed_knowledge: string[];
  forbidden_knowledge: string[];
  status: "in_progress" | "completed";
  created_at: string;
  score?: number;
  feedback?: string;
  time_complexity?: string;
  space_complexity?: string;
  improvement_suggestions?: string;
  rubric_scores_json?: string;
  reference_solution?: string;
}

export interface AlgorithmFoundationSessionListItem {
  session_id: string;
  unit_id: string;
  group_id: string;
  group_title: string;
  unit_title: string;
  target_skill: string;
  unit_kind: AlgorithmFoundationUnitKind;
  problem_id: string;
  problem_title: string;
  programming_language: string;
  status: "completed";
  created_at: string;
  score: number;
}

export interface AlgorithmFoundationSessionListResponse {
  sessions: AlgorithmFoundationSessionListItem[];
}

// --- SQL Dojo (GET/POST /sql-dojo/*) ---

export type SqlDojoDifficulty = "beginner" | "intermediate" | "advanced";

export interface SqlDojoTopicSummary {
  topic_id: string;
  topic_title: string;
  family: string;
  difficulty: SqlDojoDifficulty;
  business_domain: string;
  target_skill: string;
  attempt_count: number;
  best_score: number | null;
  last_attempted_at: string | null;
}

export interface SqlDojoThemeSummary {
  family: string;
  difficulty: SqlDojoDifficulty;
  business_domain: string;
  target_skill: string;
  title: string;
  variant_count: number;
  attempt_count: number;
  best_score: number | null;
  last_attempted_at: string | null;
  topics: SqlDojoTopicSummary[];
}

export interface SqlDojoCatalogResponse {
  difficulties: SqlDojoDifficulty[];
  themes: SqlDojoThemeSummary[];
}

export interface SqlDojoStartResponse {
  session_id: string;
  theme_family: string;
  topic_id: string | null;
  topic_title: string | null;
  difficulty: SqlDojoDifficulty;
  dialect: "postgresql";
  theme_title: string;
  business_domain: string;
  target_skill: string;
  problem_statement: string;
  schema_markdown: string;
  sample_data_json: string;
  expected_focus: string;
}

export interface SqlDojoAnswerResponse {
  session_id: string;
  score: number;
  feedback: string;
  rule_breakdown_json: string;
  improvement_suggestions: string;
  reference_sql: string;
}

export interface SqlDojoSessionResponse extends SqlDojoStartResponse {
  status: "in_progress" | "completed";
  created_at: string;
  score?: number;
  feedback?: string;
  rule_breakdown_json?: string;
  improvement_suggestions?: string;
  reference_sql?: string;
}

export interface SqlDojoSessionListItem {
  session_id: string;
  theme_family: string;
  topic_id: string | null;
  topic_title: string | null;
  difficulty: SqlDojoDifficulty;
  dialect: "postgresql";
  theme_title: string;
  status: "in_progress" | "completed";
  created_at: string;
  score?: number;
}

export interface SqlDojoSessionListResponse {
  sessions: SqlDojoSessionListItem[];
}

export interface SqlDojoQuestionResponse {
  session_id: string;
  chat_response_text: string;
}

// --- Coding Session State (from coding graph) ---

export type CodingDifficultyType =
  | "rewrite"
  | "fill_blank"
  | "bug_fix"
  | "extend"
  | "implement";

export interface CodingConfirmationPointDTO {
  id: string;
  content: string;
  start_format: CodingDifficultyType;
  end_format: CodingDifficultyType;
}

export interface CodingProblemAttemptDTO {
  confirmation_point_id: string;
  format: CodingDifficultyType;
  question_text: string;
  example_code: string;
  answer_text: string;
  score: number;
  feedback: string;
}

export interface CodingSessionStateDTO {
  session_id: string;
  roadmap_item_id: string;
  roadmap_item_level: "detail" | "middle" | "major";
  roadmap_item_title: string;
  roadmap_item_description: string;
  is_resumed: boolean;
  lecture_content?: string;
  lecture_phase_active?: boolean;
  confirmation_points?: CodingConfirmationPointDTO[];
  current_point_index?: number;
  current_question_text?: string;
  current_example_code?: string;
  current_format?: CodingDifficultyType;
  total_questions_asked?: number;
  coding_attempts?: CodingProblemAttemptDTO[];
  user_input?: string;
  input_source?: "form" | "chat";
  next_action?: "next_step" | "retry" | "next_cp" | "complete";
  current_score?: number;
  current_feedback?: string;
  chat_response_text?: string;
}

export interface CodingSessionStartResponse {
  session_id: string;
  lecture_content?: string;
  lecture_phase_active?: boolean;
}

export interface PracticeStartResponse {
  session_id: string;
  confirmation_points: CodingConfirmationPointDTO[];
  current_question_text?: string;
  current_example_code?: string;
  current_format?: CodingDifficultyType;
  current_point_index?: number;
  total_questions_asked?: number;
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
  session?: {
    id: string;
    roadmap_item_id: string;
    status: "in_progress" | "completed";
    completed_at: string | null;
  };
  graph_state?: SessionState | CodingSessionStateDTO;
}
