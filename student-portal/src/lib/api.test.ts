import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch, isAuthenticated, isFeatureLockedError, login, logout, register } from "./api";

const TOKEN_KEY = "zimfundi_student_tokens";

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("isAuthenticated", () => {
    it("is false with no stored tokens", () => {
      expect(isAuthenticated()).toBe(false);
    });

    it("is true once tokens are stored", () => {
      localStorage.setItem(TOKEN_KEY, JSON.stringify({ access: "a", refresh: "r" }));
      expect(isAuthenticated()).toBe(true);
    });
  });

  describe("login/logout", () => {
    it("stores tokens on successful login", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(jsonResponse(200, { access: "a1", refresh: "r1" })),
      );

      await login("student@example.com", "password");

      expect(isAuthenticated()).toBe(true);
      expect(JSON.parse(localStorage.getItem(TOKEN_KEY)!)).toEqual({ access: "a1", refresh: "r1" });
    });

    it("throws ApiError and does not store tokens on failed login", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(jsonResponse(401, { detail: "Invalid credentials" })),
      );

      await expect(login("student@example.com", "wrong")).rejects.toBeInstanceOf(ApiError);
      expect(isAuthenticated()).toBe(false);
    });

    it("clears tokens on logout even if the blacklist call fails", async () => {
      localStorage.setItem(TOKEN_KEY, JSON.stringify({ access: "a", refresh: "r" }));
      vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network down")));

      await logout();

      expect(isAuthenticated()).toBe(false);
    });
  });

  describe("register", () => {
    it("posts the registration payload and returns the parsed body", async () => {
      const fetchMock = vi.fn().mockResolvedValue(jsonResponse(201, { id: 1, email: "s@example.com" }));
      vi.stubGlobal("fetch", fetchMock);

      const result = await register({ email: "s@example.com", password: "password123" });

      expect(result).toEqual({ id: 1, email: "s@example.com" });
      const [, init] = fetchMock.mock.calls[0];
      expect(init.method).toBe("POST");
    });

    it("throws ApiError on a failed registration", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValue(jsonResponse(400, { email: ["Already registered"] })),
      );

      await expect(register({ email: "dup@example.com", password: "password123" })).rejects.toBeInstanceOf(
        ApiError,
      );
    });
  });

  describe("apiFetch", () => {
    it("attaches the bearer token and returns parsed JSON", async () => {
      localStorage.setItem(TOKEN_KEY, JSON.stringify({ access: "a1", refresh: "r1" }));
      const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }));
      vi.stubGlobal("fetch", fetchMock);

      const result = await apiFetch<{ ok: boolean }>("/api/v1/things/");

      expect(result).toEqual({ ok: true });
      const [, init] = fetchMock.mock.calls[0];
      expect((init.headers as Headers).get("Authorization")).toBe("Bearer a1");
    });

    it("refreshes the access token once on a 401 and retries", async () => {
      localStorage.setItem(TOKEN_KEY, JSON.stringify({ access: "stale", refresh: "r1" }));
      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(401, { detail: "expired" }))
        .mockResolvedValueOnce(jsonResponse(200, { access: "fresh", refresh: "r1" }))
        .mockResolvedValueOnce(jsonResponse(200, { ok: true }));
      vi.stubGlobal("fetch", fetchMock);

      const result = await apiFetch<{ ok: boolean }>("/api/v1/things/");

      expect(result).toEqual({ ok: true });
      expect(fetchMock).toHaveBeenCalledTimes(3);
      expect(JSON.parse(localStorage.getItem(TOKEN_KEY)!).access).toBe("fresh");
    });

    it("throws ApiError with status/body when the request ultimately fails", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(500, { detail: "boom" })));

      const error = await apiFetch("/api/v1/things/").catch((e) => e);

      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).status).toBe(500);
      expect((error as ApiError).body).toEqual({ detail: "boom" });
    });

    it("returns undefined for a 204 No Content response", async () => {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 204 })));

      const result = await apiFetch("/api/v1/things/1/");

      expect(result).toBeUndefined();
    });
  });

  describe("isFeatureLockedError", () => {
    it("recognizes a 403 feature_locked payload", () => {
      const error = new ApiError(403, {
        error: { code: "feature_locked", message: "Upgrade required", upgrade_url: "/billing" },
      });

      expect(isFeatureLockedError(error)).toBe(true);
    });

    it("rejects unrelated errors", () => {
      expect(isFeatureLockedError(new ApiError(403, { error: { code: "other" } }))).toBe(false);
      expect(isFeatureLockedError(new ApiError(404, { error: { code: "feature_locked" } }))).toBe(false);
      expect(isFeatureLockedError(new Error("plain error"))).toBe(false);
    });
  });
});
