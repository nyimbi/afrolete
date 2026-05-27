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
