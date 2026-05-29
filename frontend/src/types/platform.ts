export type CapabilityStatus = "not-started" | "foundation" | "partial" | "complete";

export type PlatformCapability = {
  key: string;
  name: string;
  status: CapabilityStatus;
  description: string;
};

export type InfrastructureComponent = {
  key: string;
  name: string;
  status: string;
  mode: string;
  configured: boolean;
  endpoint: string | null;
  details: string[];
};

export type InfrastructureStatus = {
  environment: string;
  components: InfrastructureComponent[];
};

export type InfrastructureProbeResult = {
  key: string;
  name: string;
  status: string;
  reachable: boolean | null;
  latency_ms: number | null;
  checked_at: string;
  details: string[];
};

export type InfrastructureProbeSummary = {
  environment: string;
  timeout_seconds: number;
  results: InfrastructureProbeResult[];
};

export type AuthEndpointRead = {
  key: string;
  name: string;
  url: string | null;
  required: boolean;
  configured: boolean;
};

export type AuthReadiness = {
  mode: string;
  provider: string;
  issuer: string | null;
  audience: string | null;
  status: string;
  endpoints: AuthEndpointRead[];
  blockers: string[];
  warnings: string[];
  next_actions: string[];
};

export type AuthorizationResourceRead = {
  resource_type: string;
  relations: string[];
  permissions: string[];
  notes: string[];
};

export type AuthorizationReadiness = {
  mode: string;
  provider: string;
  status: string;
  endpoint: string | null;
  insecure_transport: boolean;
  schema_hash: string | null;
  schema_path: string | null;
  resources: AuthorizationResourceRead[];
  relationship_count: number;
  permission_count: number;
  blockers: string[];
  warnings: string[];
  next_actions: string[];
};

export type AuthorizationSchemaRead = {
  path: string;
  sha256: string;
  resource_types: string[];
  relation_count: number;
  permission_count: number;
  content: string;
};
