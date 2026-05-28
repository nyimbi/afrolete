export type UUID = string;
export type ISODateTime = string;

export interface AfroLeteClientOptions {
  baseUrl: string;
  apiKey: string;
  fetch?: typeof fetch;
}

export interface AfroLeteRequestErrorDetails {
  status: number;
  statusText: string;
  body: unknown;
}

export class AfroLeteRequestError extends Error {
  readonly status: number;
  readonly statusText: string;
  readonly body: unknown;

  constructor(details: AfroLeteRequestErrorDetails) {
    super(`AfroLete request failed with ${details.status} ${details.statusText}`);
    this.name = "AfroLeteRequestError";
    this.status = details.status;
    this.statusText = details.statusText;
    this.body = details.body;
  }
}

export interface DeveloperApiKeyInspection {
  valid: boolean;
  organization_id: UUID;
  application_id: UUID;
  api_key_id: UUID;
  client_id: string;
  application_name: string;
  environment: string;
  scopes: string[];
  rate_limit_per_minute: number;
  usage_count: number;
  window_started_at: ISODateTime | null;
  window_request_count: number;
}

export interface Organization {
  id: UUID;
  name: string;
  slug: string;
  organization_type: string;
  association_level: string | null;
  country_code: string | null;
  primary_sport: string | null;
  mission: string | null;
  public_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  website_url: string | null;
  subdomain: string | null;
  logo_url: string | null;
  brand_primary_color: string | null;
  brand_secondary_color: string | null;
  my_roles: string[];
}

export interface Event {
  id: UUID;
  organization_id: UUID;
  team_id: UUID | null;
  event_type: string;
  title: string;
  starts_at: ISODateTime;
  ends_at: ISODateTime | null;
  timezone: string | null;
  venue_name: string | null;
  notes: string | null;
}

export interface Team {
  id: UUID;
  organization_id: UUID;
  name: string;
  sport: string;
  sport_format: string;
  age_group: string | null;
  gender_category: string | null;
  season_label: string | null;
}

export interface EventCreate {
  organization_id: UUID;
  team_id?: UUID | null;
  event_type: string;
  title: string;
  starts_at: ISODateTime;
  ends_at?: ISODateTime | null;
  timezone?: string | null;
  venue_name?: string | null;
  notes?: string | null;
}

export interface TrainingDrill {
  id: UUID;
  organization_id: UUID;
  sport: string;
  name: string;
  focus_area: string;
  category: string;
  min_age: number | null;
  max_age: number | null;
  equipment: string | null;
  description: string | null;
  coaching_points: string | null;
  default_duration_minutes: number | null;
  default_intensity: number | null;
  status: string;
}

export interface TrainingDrillCreate {
  organization_id: UUID;
  sport: string;
  name: string;
  focus_area: string;
  category: string;
  min_age?: number | null;
  max_age?: number | null;
  equipment?: string | null;
  description?: string | null;
  coaching_points?: string | null;
  default_duration_minutes?: number | null;
  default_intensity?: number | null;
  status?: string;
}

interface QueryValue {
  toString(): string;
}

type QueryParams = Record<string, QueryValue | null | undefined>;

export class AfroLeteClient {
  readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly fetcher: typeof fetch;

  readonly organization = {
    get: (params: { organizationId: UUID }): Promise<Organization> =>
      this.request<Organization>("/organization", {
        query: { organization_id: params.organizationId },
      }),
  };

  readonly events = {
    list: (params: { organizationId: UUID; teamId?: UUID | null }): Promise<Event[]> =>
      this.request<Event[]>("/events", {
        query: { organization_id: params.organizationId, team_id: params.teamId },
      }),
    create: (payload: EventCreate): Promise<Event> =>
      this.request<Event>("/events", {
        method: "POST",
        body: payload,
      }),
  };

  readonly teams = {
    list: (params: { organizationId: UUID }): Promise<Team[]> =>
      this.request<Team[]>("/teams", {
        query: { organization_id: params.organizationId },
      }),
  };

  readonly training = {
    drills: {
      list: (params: { organizationId: UUID; sport?: string | null }): Promise<TrainingDrill[]> =>
        this.request<TrainingDrill[]>("/training/drills", {
          query: { organization_id: params.organizationId, sport: params.sport },
        }),
      create: (payload: TrainingDrillCreate): Promise<TrainingDrill> =>
        this.request<TrainingDrill>("/training/drills", {
          method: "POST",
          body: payload,
        }),
    },
  };

  constructor(options: AfroLeteClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.apiKey = options.apiKey;
    this.fetcher = options.fetch ?? fetch;
  }

  me(): Promise<DeveloperApiKeyInspection> {
    return this.request<DeveloperApiKeyInspection>("/me");
  }

  private async request<T>(
    path: string,
    options: {
      method?: "GET" | "POST";
      query?: QueryParams;
      body?: unknown;
    } = {},
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}/api/v1/sdk${path}`);
    for (const [key, value] of Object.entries(options.query ?? {})) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, value.toString());
      }
    }

    const headers: HeadersInit = {
      Accept: "application/json",
      "X-Afrolete-API-Key": this.apiKey,
    };
    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
    }

    const requestInit: RequestInit = {
      method: options.method ?? "GET",
      headers,
    };
    if (options.body !== undefined) {
      requestInit.body = JSON.stringify(options.body);
    }

    const response = await this.fetcher(url, requestInit);
    const body = await parseJsonResponse(response);
    if (!response.ok) {
      throw new AfroLeteRequestError({
        status: response.status,
        statusText: response.statusText,
        body,
      });
    }
    return body as T;
  }
}

async function parseJsonResponse(response: Response): Promise<unknown> {
  const text = await response.text();
  if (text.length === 0) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}
