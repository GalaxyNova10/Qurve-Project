// QURVE API Client — points to local FastAPI backend
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`API ${response.status} ${response.statusText} — ${body}`);
  }

  // Handle 204 No Content
  if (response.status === 204) return undefined as T;

  return response.json() as Promise<T>;
}

export const api = {
  // Health check
  health: () => request<{ status: string; timestamp: string }>("/health"),

  // Example: submit portfolio optimization
  // optimize: (payload: unknown) =>
  //   request<{ job_id: string }>("/api/v1/optimize", {
  //     method: "POST",
  //     body: JSON.stringify(payload),
  //   }),

  // Example: get job status
  // getJob: (jobId: string) =>
  //   request<unknown>(`/api/v1/jobs/${jobId}`),

  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
};

export { BASE_URL };
