export type ApiError = {
  status: number;
  detail: unknown;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function apiRequest<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.token) headers.set("Authorization", `Bearer ${options.token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail: unknown = response.statusText;
    try {
      detail = await response.json();
    } catch {
      // Keep status text when the response is not JSON.
    }
    throw { status: response.status, detail } satisfies ApiError;
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    display_name: string | null;
  };
};

export type TodayPlan = {
  id: string;
  plan_date: string;
  default_view_mode: "timeline" | "list";
  capacity_snapshot: Record<string, unknown>;
  summary: string | null;
  status: string;
  generated_at: string;
  items: Array<{
    id: string;
    task_id: string | null;
    item_id: string | null;
    title_snapshot: string;
    suggested_start: string | null;
    suggested_end: string | null;
    do_window_start: string | null;
    do_window_end: string | null;
    block_type: string;
    position: number;
    is_fixed_time: boolean;
    is_optional: boolean;
    status: string;
    reason_selected: string | null;
  }>;
};

export type ProposedChange = {
  id: string;
  source_type: string;
  source_id: string | null;
  change_type: string;
  status: "pending" | "accepted" | "rejected" | "expired";
  title: string;
  rationale: string | null;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ProposedChangeDecision = {
  proposed_change: ProposedChange;
  plan_item: TodayPlan["items"][number] | null;
  message: string;
};

export type Domain = {
  id: string;
  name: string;
  description: string | null;
  weight: string | number;
  active: boolean;
  project_count: number;
};

export type Project = {
  id: string;
  domain_id: string | null;
  title: string;
  desired_outcome: string | null;
  status: string;
  deadline: string | null;
  notes: string | null;
};

export type Task = {
  id: string;
  domain_id: string | null;
  project_id: string | null;
  title: string;
  notes: string | null;
  status: string;
  priority: string;
  due_at: string | null;
  do_window_start: string | null;
  do_window_end: string | null;
  effort_estimate_minutes: number | null;
  energy_required: string | null;
};

export type Routine = {
  id: string;
  domain_id: string | null;
  title: string;
  notes: string | null;
  recurrence_rule: string;
  preferred_time_window: Record<string, unknown>;
  effort_estimate_minutes: number | null;
  energy_required: string | null;
  active: boolean;
};

export type DailyReviewPrompt = {
  review_date: string;
  prompts: Array<{
    plan_item_id: string;
    task_id: string | null;
    title: string;
    prompt_type: string;
    question: string;
    importance_score: number;
  }>;
  quick_checks: string[];
};

export type WeeklyPlan = {
  id: string;
  week_start_date: string;
  generated_at: string;
  summary: string | null;
  focus_notes: string | null;
  capacity_snapshot: Record<string, unknown>;
  status: string;
  accepted_at: string | null;
  daily_plans: TodayPlan[];
};

export type AIAction = {
  id: string;
  source_type: string;
  source_id: string | null;
  action_type: string;
  target_type: string;
  target_id: string | null;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  reason: string | null;
  reversible: boolean;
  created_at: string;
};

export type UserProfile = {
  timezone: string;
  default_tone: "terse" | "warm" | "direct";
  preferred_day_view: "timeline" | "list";
  wake_time: string | null;
  sleep_time: string | null;
  work_hours: Record<string, unknown>;
  planning_style: string | null;
  review_style: string | null;
  ai_change_visibility: "quiet" | "digest" | "prompt";
};

export type LearnedCapabilityProfile = {
  weekday_focus_minutes_typical: number | null;
  weekend_focus_minutes_typical: number | null;
  weekday_maintenance_minutes_typical: number | null;
  weekend_maintenance_minutes_typical: number | null;
  morning_reliability: number | null;
  afternoon_reliability: number | null;
  evening_reliability: number | null;
  plan_completion_rate_14d: number | null;
  plan_completion_rate_30d: number | null;
  routine_completion_rate_14d: number | null;
  overload_sensitivity: number | null;
  confidence_score: number;
  updated_at: string;
};
