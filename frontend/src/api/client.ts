const BASE_URL = "/api";

class ApiClient {
  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${BASE_URL}${path}`;
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(error.detail || `Request failed: ${res.status}`);
    }
    return res.json();
  }

  get<T>(path: string, params?: Record<string, unknown>): Promise<T> {
    const search = params
      ? "?" + new URLSearchParams(
          Object.entries(params)
            .filter(([, v]) => v !== undefined && v !== null && v !== "")
            .map(([k, v]) => [k, String(v)])
        ).toString()
      : "";
    const pathWithSlash = search && !path.endsWith("/") ? `${path}/` : path;
    return this.request<T>(`${pathWithSlash}${search}`);
  }

  post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }
}

export const apiClient = new ApiClient();