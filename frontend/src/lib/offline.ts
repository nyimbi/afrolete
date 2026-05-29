import { getStoredAuthSession } from "@/lib/auth";
import { apiBaseUrl } from "@/lib/config";
import type { LocalIdentity } from "@/types/operations";

const QUEUE_KEY = "afrolete.offlineOutbox.v1";
const listeners = new Set<(snapshot: OfflineQueueSnapshot) => void>();

export type OfflineQueueItem = {
  id: string;
  label: string;
  path: string;
  method: string;
  body: unknown;
  identity?: LocalIdentity;
  headers: Record<string, string>;
  created_at: string;
  attempt_count: number;
  last_error: string | null;
  idempotency_key: string;
};

export type OfflineQueueSnapshot = {
  online: boolean;
  pending_count: number;
  last_error: string | null;
  last_flushed_at: string | null;
  service_worker_ready: boolean;
  items: OfflineQueueItem[];
};

export type QueueOfflineRequestInput = {
  label: string;
  path: string;
  method: string;
  body: unknown;
  identity?: LocalIdentity;
  headers: Headers;
  idempotencyKey?: string;
};

export type OfflineFlushResult = {
  attempted: number;
  succeeded: number;
  failed: number;
  remaining: number;
};

let lastError: string | null = null;
let lastFlushedAt: string | null = null;
let serviceWorkerReady = false;

export function getOfflineQueueSnapshot(): OfflineQueueSnapshot {
  return {
    online: typeof navigator === "undefined" ? true : navigator.onLine,
    pending_count: readQueue().length,
    last_error: lastError,
    last_flushed_at: lastFlushedAt,
    service_worker_ready: serviceWorkerReady,
    items: readQueue()
  };
}

export function subscribeOfflineQueue(listener: (snapshot: OfflineQueueSnapshot) => void) {
  listeners.add(listener);
  listener(getOfflineQueueSnapshot());
  return () => {
    listeners.delete(listener);
  };
}

export async function registerOfflineServiceWorker(): Promise<void> {
  if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) {
    serviceWorkerReady = false;
    notify();
    return;
  }
  try {
    await navigator.serviceWorker.register("/sw.js");
    serviceWorkerReady = true;
    notify();
  } catch (error) {
    serviceWorkerReady = false;
    lastError = error instanceof Error ? error.message : "Service worker registration failed";
    notify();
  }
}

export function installOfflineQueueListeners(onOnline?: () => void) {
  if (typeof window === "undefined") {
    return () => undefined;
  }
  const handleOnline = () => {
    notify();
    onOnline?.();
  };
  const handleOffline = () => notify();
  window.addEventListener("online", handleOnline);
  window.addEventListener("offline", handleOffline);
  return () => {
    window.removeEventListener("online", handleOnline);
    window.removeEventListener("offline", handleOffline);
  };
}

export function queueOfflineRequest(input: QueueOfflineRequestInput): OfflineQueueItem {
  const queue = readQueue();
  const idempotencyKey = input.idempotencyKey ?? `${input.method}:${input.path}:${Date.now()}`;
  const existing = queue.find((item) => item.idempotency_key === idempotencyKey);
  if (existing) {
    return existing;
  }
  const item: OfflineQueueItem = {
    id: crypto.randomUUID(),
    label: input.label,
    path: input.path,
    method: input.method,
    body: input.body,
    identity: input.identity,
    headers: headersToRecord(input.headers),
    created_at: new Date().toISOString(),
    attempt_count: 0,
    last_error: null,
    idempotency_key: idempotencyKey
  };
  writeQueue([...queue, item]);
  notify();
  return item;
}

export async function flushOfflineQueue(): Promise<OfflineFlushResult> {
  const queue = readQueue();
  if (queue.length === 0) {
    lastError = null;
    lastFlushedAt = new Date().toISOString();
    notify();
    return { attempted: 0, succeeded: 0, failed: 0, remaining: 0 };
  }
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    return { attempted: 0, succeeded: 0, failed: 0, remaining: queue.length };
  }

  const remaining: OfflineQueueItem[] = [];
  let succeeded = 0;
  let failed = 0;
  for (const item of queue) {
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1${item.path}`, {
        method: item.method,
        headers: replayHeaders(item),
        body: item.body === undefined ? undefined : JSON.stringify(item.body)
      });
      if (!response.ok) {
        throw new Error(`Replay failed with ${response.status}`);
      }
      succeeded += 1;
    } catch (error) {
      failed += 1;
      remaining.push({
        ...item,
        attempt_count: item.attempt_count + 1,
        last_error: error instanceof Error ? error.message : "Replay failed"
      });
    }
  }

  lastError = remaining[0]?.last_error ?? null;
  lastFlushedAt = new Date().toISOString();
  writeQueue(remaining);
  notify();
  return { attempted: queue.length, succeeded, failed, remaining: remaining.length };
}

function replayHeaders(item: OfflineQueueItem): Headers {
  const headers = new Headers(item.headers);
  headers.set("Accept", "application/json");
  if (item.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  const session = getStoredAuthSession();
  if (session) {
    headers.set("Authorization", `Bearer ${session.accessToken}`);
  }
  if (item.identity) {
    headers.set("X-Afrolete-Sub", item.identity.sub);
    headers.set("X-Afrolete-Email", item.identity.email);
    headers.set("X-Afrolete-Name", item.identity.name);
  }
  headers.set("Idempotency-Key", item.idempotency_key);
  headers.set("X-Afrolete-Offline-Replay", "true");
  return headers;
}

function readQueue(): OfflineQueueItem[] {
  if (typeof window === "undefined") {
    return [];
  }
  const raw = window.localStorage.getItem(QUEUE_KEY);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw) as OfflineQueueItem[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    window.localStorage.removeItem(QUEUE_KEY);
    return [];
  }
}

function writeQueue(queue: OfflineQueueItem[]): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

function headersToRecord(headers: Headers): Record<string, string> {
  const record: Record<string, string> = {};
  headers.forEach((value, key) => {
    if (key.toLowerCase() !== "authorization") {
      record[key] = value;
    }
  });
  return record;
}

function notify(): void {
  const snapshot = getOfflineQueueSnapshot();
  listeners.forEach((listener) => listener(snapshot));
}
