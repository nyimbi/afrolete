import { apiBaseUrl } from "@/lib/config";
import { getStoredAuthSession } from "@/lib/auth";
import { queueOfflineRequest, type OfflineQueueItem } from "@/lib/offline";
import type { LocalIdentity } from "@/types/operations";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(errorMessage(detail));
    this.status = status;
    this.detail = detail;
  }
}

export class OfflineQueueError extends Error {
  item: OfflineQueueItem;

  constructor(item: OfflineQueueItem) {
    super(`${item.label} queued for offline replay`);
    this.item = item;
  }
}

type RequestOptions = Omit<RequestInit, "body" | "headers"> & {
  body?: unknown;
  identity?: LocalIdentity;
  headers?: HeadersInit;
  offlineQueue?: {
    enabled: boolean;
    label: string;
    idempotencyKey?: string;
  };
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers: inputHeaders, identity, offlineQueue, ...requestOptions } = options;
  const headers = new Headers(inputHeaders);
  headers.set("Accept", "application/json");

  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const session = getStoredAuthSession();
  if (session) {
    headers.set("Authorization", `Bearer ${session.accessToken}`);
  }

  if (identity) {
    headers.set("X-Afrolete-Sub", identity.sub);
    headers.set("X-Afrolete-Email", identity.email);
    headers.set("X-Afrolete-Name", identity.name);
  }

  if (offlineQueue?.enabled && isOfflineMutation(requestOptions.method)) {
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      throw new OfflineQueueError(queueOfflineRequest({
        label: offlineQueue.label,
        path,
        method: requestOptions.method ?? "POST",
        body,
        identity,
        headers,
        idempotencyKey: offlineQueue.idempotencyKey
      }));
    }
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
      ...requestOptions,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body)
    });
  } catch (error) {
    if (offlineQueue?.enabled && isOfflineMutation(requestOptions.method)) {
      throw new OfflineQueueError(queueOfflineRequest({
        label: offlineQueue.label,
        path,
        method: requestOptions.method ?? "POST",
        body,
        identity,
        headers,
        idempotencyKey: offlineQueue.idempotencyKey
      }));
    }
    throw error;
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readBody(response));
  }

  return (await response.json()) as T;
}

export async function apiDownload(path: string, options: RequestOptions = {}): Promise<{ blob: Blob; filename: string }> {
  const { body: _body, headers: inputHeaders, identity, ...requestOptions } = options;
  const headers = new Headers(inputHeaders);
  headers.set("Accept", "*/*");

  const session = getStoredAuthSession();
  if (session) {
    headers.set("Authorization", `Bearer ${session.accessToken}`);
  }

  if (identity) {
    headers.set("X-Afrolete-Sub", identity.sub);
    headers.set("X-Afrolete-Email", identity.email);
    headers.set("X-Afrolete-Name", identity.name);
  }

  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    ...requestOptions,
    headers
  });

  if (!response.ok) {
    throw new ApiError(response.status, await readBody(response));
  }

  return {
    blob: await response.blob(),
    filename: filenameFromContentDisposition(response.headers.get("Content-Disposition")) ?? "afrolete-download"
  };
}

function filenameFromContentDisposition(value: string | null): string | null {
  if (!value) {
    return null;
  }
  const match = /filename="?([^";]+)"?/i.exec(value);
  return match?.[1] ?? null;
}

function isOfflineMutation(method?: string): boolean {
  const normalized = (method ?? "GET").toUpperCase();
  return normalized === "POST" || normalized === "PUT" || normalized === "PATCH";
}

async function readBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return response.statusText;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function errorMessage(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }

  if (detail && typeof detail === "object" && "detail" in detail) {
    const value = (detail as { detail: unknown }).detail;
    if (typeof value === "string") {
      return value;
    }
    return JSON.stringify(value);
  }

  return "Request failed";
}
