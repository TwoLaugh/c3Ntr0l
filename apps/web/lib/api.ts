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
  items: Array<{
    id: string;
    task_id: string | null;
    title_snapshot: string;
    suggested_start: string | null;
    suggested_end: string | null;
    block_type: string;
    status: string;
    reason_selected: string | null;
  }>;
};
