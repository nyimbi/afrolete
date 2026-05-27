# AfroLete Implementation Roadmap

This roadmap preserves the full product ambition while forcing delivery through
working vertical slices.

## Principles

- Build production-shaped slices, not throwaway demos.
- Keep AI agents in the model from the beginning.
- Make authorization explicit through SpiceDB.
- Keep UI/UX quality part of acceptance, not a finishing pass.
- Commit and push verified work regularly.

## Slice Order

### Slice 001 - Executable SaaS Foundation

Goal: make the repository runnable and establish the platform spine.

- FastAPI app boot, settings, health route.
- Initial SQLAlchemy model set for identity, organizations, teams, athletes,
  guardians, events, attendance, and AI agents.
- Alembic baseline setup.
- SpiceDB schema starter.
- OpenBao/Postgres/Keycloak setup notes.
- Next/TypeScript frontend shell.
- First progress log entry.

### Slice 002 - Identity, Tenant, And Authorization Vertical

- Keycloak JWT validation.
- `app_users` identity bridge.
- Organization creation and membership APIs.
- SpiceDB writes for org ownership/admin/member roles.
- Frontend organization onboarding flow.
- Tests for authn/authz behavior.

### Slice 003 - Teams, Athletes, Guardians, And Staff

- Team and roster APIs.
- Athlete profile APIs.
- Guardian relationship APIs.
- Staff assignment APIs.
- UI for roster management and athlete profiles.

### Slice 004 - Events And Attendance

- Event scheduling APIs.
- RSVP and attendance APIs.
- Attendance dashboard and mobile-friendly check-in UI.
- Notifications boundary.

### Slice 005 - Performance And Coaching

- Assessment schemas and APIs.
- Metrics ingestion.
- Goal tracking.
- Training plan and drill library foundation.
- Coach dashboards.

### Slice 006 - Communications, Consent, And Safeguarding

- Announcements and direct messages.
- Consent templates and signing flows.
- Incident reporting.
- Safeguarding/audit workflows.

### Slice 007 - Competition And Event Operations

- Fixtures, leagues, tournaments, standings.
- Officials and venues.
- Multi-sport event management.
- Ticketing and awards foundations.

### Slice 008 - Assets, Facilities, Finance, And Sponsorship

- Equipment and facility management.
- Subscriptions, fees, fundraising, sponsorship activation.
- Financial reports and exports.

### Slice 009 - AI Agents And Intelligence

- Agent registry and permissions.
- Agent task orchestration.
- Human review queues.
- Video/audio/text ingestion pipelines.
- Reports and insight generation.

### Slice 010 - Integrations And Scale

- Webhooks and external API platform.
- Device/video/school/finance integrations.
- Observability, deployment hardening, and SaaS operations.

