const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

type Tokens = { access: string; refresh: string };

const TOKEN_KEY = "zimsec_student_tokens";

function getTokens(): Tokens | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(TOKEN_KEY);
  return raw ? (JSON.parse(raw) as Tokens) : null;
}

function setTokens(tokens: Tokens | null) {
  if (typeof window === "undefined") return;
  if (tokens) localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`API request failed with status ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function parseErrorBody(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

async function refreshAccessToken(): Promise<string | null> {
  const tokens = getTokens();
  if (!tokens?.refresh) return null;

  const res = await fetch(`${API_BASE}/api/v1/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: tokens.refresh }),
  });
  if (!res.ok) {
    setTokens(null);
    return null;
  }
  const data = await res.json();
  setTokens({ access: data.access, refresh: tokens.refresh });
  return data.access as string;
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;

  const doFetch = async (accessToken?: string) => {
    const headers = new Headers(options.headers);
    if (!isFormData) headers.set("Content-Type", "application/json");
    if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
    return fetch(url, { ...options, headers });
  };

  const tokens = getTokens();
  let res = await doFetch(tokens?.access);

  if (res.status === 401 && tokens?.refresh) {
    const newAccess = await refreshAccessToken();
    if (newAccess) res = await doFetch(newAccess);
  }

  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorBody(res));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE}/api/v1/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new ApiError(res.status, await parseErrorBody(res));
  const data = await res.json();
  setTokens({ access: data.access, refresh: data.refresh });
}

export async function register(input: {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
}) {
  const res = await fetch(`${API_BASE}/api/v1/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new ApiError(res.status, await parseErrorBody(res));
  return res.json();
}

export async function logout() {
  const tokens = getTokens();
  setTokens(null);
  if (!tokens?.refresh) return;
  try {
    await fetch(`${API_BASE}/api/v1/auth/logout/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${tokens.access}` },
      body: JSON.stringify({ refresh: tokens.refresh }),
    });
  } catch {
    // Best-effort: token is already cleared client-side even if the blacklist call fails.
  }
}

export type FeatureLockedError = {
  code: "feature_locked";
  message: string;
  upgrade_url: string;
};

export function isFeatureLockedError(error: unknown): error is ApiError & {
  body: { error: FeatureLockedError };
} {
  return (
    error instanceof ApiError &&
    error.status === 403 &&
    typeof error.body === "object" &&
    error.body !== null &&
    (error.body as { error?: { code?: string } }).error?.code === "feature_locked"
  );
}

export function isAuthenticated() {
  return getTokens() !== null;
}
