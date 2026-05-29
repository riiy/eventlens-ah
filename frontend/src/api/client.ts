const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

class ApiClient {
  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const url = `${BASE_URL}${path}`;
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    });

    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");

    if (!res.ok) {
      if (isJson) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `Request failed: ${res.status}`);
      }

      const text = await res.text().catch(() => "");
      throw new Error(this.formatNonJsonError(url, res.status, text));
    }

    if (!isJson) {
      const text = await res.text().catch(() => "");
      throw new Error(this.formatNonJsonError(url, res.status, text));
    }

    return res.json();
  }

  private formatNonJsonError(url: string, status: number, text: string): string {
    const preview = text.trim().replace(/\s+/g, " ").slice(0, 120);
    const looksLikeHtml = preview.startsWith("<!DOCTYPE") || preview.startsWith("<html");
    const detail = looksLikeHtml
      ? "received HTML instead of JSON; check the frontend proxy or backend API route"
      : `received non-JSON response${preview ? `: ${preview}` : ""}`;
    return `API request failed (${status}) for ${url}: ${detail}`;
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
