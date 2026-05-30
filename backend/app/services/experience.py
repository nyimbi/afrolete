import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experience import ProductHelpInteraction, ProductTourProgress
from app.models.identity import Person
from app.models.organization import Organization
from app.schemas.experience import ProductTourProgressCreate, ProductTourStepUpdate
from app.services.auth.identity_bridge import CurrentIdentity
from app.services.authz.service import AuthorizationService
from app.services.training import ensure_manage_training


def product_tour_catalog() -> list[dict[str, object]]:
    return [
        {
            "key": "video_analysis_tour",
            "surface": "performance",
            "role": "coach",
            "title": "Video Analysis Made Easy",
            "estimated_minutes": 15,
            "objective": "Practice uploading footage, tagging players, choosing metrics, and reviewing coaching guidance.",
            "steps": [
                tour_step("upload_video", "Upload video", "#performance", "Upload or select a match/training clip.", "Choose a demo clip and confirm the analysis focus.", "A video asset is ready for analysis.", 40),
                tour_step("tag_players", "Tag players", "#performance", "Assign track labels or jersey numbers before sharing player guidance.", "Select a track and confirm identity review.", "At least one player identity is confirmed.", 55),
                tour_step("choose_metrics", "Choose metrics", "#performance", "Pick distance, sprint, tactical, pose, or gait evidence for the review.", "Set the metrics that matter for the session.", "The analysis run has a clear coaching purpose.", 50),
                tour_step("review_guidance", "Review guidance", "#performance", "Read the AI-generated cues with quality warnings visible.", "Mark one coaching cue as ready for player discussion.", "Coach review is complete before player sharing.", 65),
            ],
        },
        {
            "key": "registration_launch_tour",
            "surface": "registration",
            "role": "administrator",
            "title": "Launch Registration",
            "estimated_minutes": 12,
            "objective": "Open a branded registration flow, collect packets, and move families into admissions.",
            "steps": [
                tour_step("brand_site", "Brand the site", "#organizations", "Confirm public name, colors, contact details, and registration policy.", "Open the public site preview.", "The public site has tenant branding.", 40),
                tour_step("share_link", "Share registration", "#organizations", "Copy the hosted registration link or QR payload.", "Prepare one campaign message.", "Families can access the correct packet.", 45),
                tour_step("review_packet", "Review packet", "#admissions", "Check documents, payment, guardian account readiness, and consent.", "Open a pending inquiry and inspect readiness.", "Staff know what blocks conversion.", 55),
            ],
        },
        {
            "key": "training_command_tour",
            "surface": "training",
            "role": "coach",
            "title": "Training Command Center",
            "estimated_minutes": 10,
            "objective": "Turn readiness, load, availability, and agent drafts into a weekly coaching plan.",
            "steps": [
                tour_step("build_plan", "Build a plan", "#training", "Create or generate a weekly plan from readiness and competition context.", "Generate one AI-assisted plan.", "A plan exists with blocks and load guidance.", 50),
                tour_step("schedule_session", "Schedule session", "#training", "Use availability suggestions before locking a session.", "Apply a suggested slot.", "The session avoids obvious conflicts.", 45),
                tour_step("record_feedback", "Record feedback", "#training", "Capture RPE, readiness, soreness, and coach notes after training.", "Submit one feedback record.", "The next plan has evidence to adapt safely.", 60),
            ],
        },
        {
            "key": "guardian_consent_tour",
            "surface": "safeguarding",
            "role": "safeguarding_lead",
            "title": "Guardian Consent and Clearance",
            "estimated_minutes": 11,
            "objective": "Issue consent, collect guardian responses, and enforce minor participation gates.",
            "steps": [
                tour_step("create_consent", "Create consent request", "#safeguarding", "Generate an event or travel consent request for a minor.", "Send a consent link through a supported channel.", "A guardian has a one-use response path.", 45),
                tour_step("review_clearance", "Review clearance", "#safeguarding", "Check attendance, medical, travel, and consent blockers.", "Open the family clearance card.", "Staff can see whether the athlete may participate.", 55),
                tour_step("audit_evidence", "Audit evidence", "#safeguarding", "Review signed evidence and status history before escalation.", "Open the evidence record.", "The decision has traceable evidence.", 60),
            ],
        },
    ]


def tour_step(
    key: str,
    title: str,
    target: str,
    instruction: str,
    practice_task: str,
    success_criteria: str,
    xp: int,
) -> dict[str, object]:
    return {
        "key": key,
        "title": title,
        "target": target,
        "instruction": instruction,
        "practice_task": practice_task,
        "success_criteria": success_criteria,
        "xp": xp,
    }


def product_help_articles() -> list[dict[str, object]]:
    return [
        article(
            "understanding_als",
            "performance",
            "coach",
            "Understanding AfroLete Score",
            "Read ALS as a coaching story, not a single verdict.",
            "ALS combines physical, technical, tactical, mental, wellness, trend, and evidence signals. Coaches should pair the score with confidence, provenance, and recent workload before prescribing changes.",
            ["als", "score", "performance", "readiness"],
            "video_analysis_tour",
            "Open performance review",
            "#performance",
        ),
        article(
            "match_tracking_quality",
            "performance",
            "coach",
            "When Match Tracking Is Shareable",
            "Use calibration, identity review, sample coverage, and quality warnings before sharing player metrics.",
            "Raw OpenCV tracking is useful for demos and coaching exploration. Player-facing guidance should pass calibration, tracking quality, identity continuity, and sample-window checks.",
            ["video", "tracking", "distance", "quality"],
            "video_analysis_tour",
            "Review tracking evidence",
            "#performance",
        ),
        article(
            "registration_readiness",
            "registration",
            "administrator",
            "Registration Packet Readiness",
            "Staff should resolve documents, payment, guardian identity, and consent before conversion.",
            "The admissions queue highlights packet completeness, guardian account readiness, payment settlement, and missing verification steps so conversion creates clean athlete and family records.",
            ["registration", "admissions", "guardian", "payment"],
            "registration_launch_tour",
            "Open admissions",
            "#organizations",
        ),
        article(
            "training_command_center",
            "training",
            "coach",
            "Training Command Center Signals",
            "Use readiness, load delta, availability, feedback, and agent drafts together.",
            "The command center is designed for repeated weekly use: generate a plan, schedule sessions, record feedback, and queue the Training Strategy Agent when evidence suggests an adjustment.",
            ["training", "load", "readiness", "agent"],
            "training_command_tour",
            "Open training",
            "#training",
        ),
        article(
            "guardian_consent_channels",
            "safeguarding",
            "safeguarding_lead",
            "Guardian Consent Channels",
            "Consent can be captured through one-use web links, SMS, WhatsApp, Telegram, email, or staff entry.",
            "Every consent response should map back to the request, guardian identity, channel, status, and event/travel clearance so attendance gates have auditable evidence.",
            ["consent", "guardian", "minor", "safeguarding"],
            "guardian_consent_tour",
            "Open safeguarding",
            "#safeguarding",
        ),
    ]


def article(
    key: str,
    surface: str,
    role: str,
    title: str,
    summary: str,
    body: str,
    tags: list[str],
    related_tour_key: str,
    action_label: str,
    action_href: str,
) -> dict[str, object]:
    return {
        "key": key,
        "surface": surface,
        "role": role,
        "title": title,
        "summary": summary,
        "body": body,
        "tags": tags,
        "related_tour_key": related_tour_key,
        "action_label": action_label,
        "action_href": action_href,
    }


def product_experience_catalog(surface: str | None = None, role: str | None = None) -> dict[str, object]:
    return {
        "tours": filter_catalog(product_tour_catalog(), surface, role),
        "articles": filter_catalog(product_help_articles(), surface, role),
    }


async def start_product_tour_progress(
    db: AsyncSession,
    identity: CurrentIdentity,
    payload: ProductTourProgressCreate,
    authz: AuthorizationService,
) -> ProductTourProgress:
    await get_organization(db, payload.organization_id)
    await ensure_manage_training(authz, identity, payload.organization_id)
    tour = product_tour(payload.tour_key)
    steps = [dict(step) for step in tour["steps"]]
    existing = await db.scalar(
        select(ProductTourProgress)
        .where(ProductTourProgress.organization_id == payload.organization_id)
        .where(ProductTourProgress.person_id == identity.person_id)
        .where(ProductTourProgress.tour_key == str(tour["key"]))
        .limit(1)
    )
    now = datetime.now(UTC)
    first_step = str(steps[0]["key"]) if steps else None
    if existing is not None:
        if payload.restart:
            existing.completed_steps_json = "[]"
            existing.skipped_steps_json = "[]"
            existing.score = 0
            existing.star_count = 0
            existing.status = "active"
            existing.completed_at = None
            existing.current_step_key = first_step
        existing.surface = payload.surface or str(tour["surface"])
        existing.role = payload.role
        existing.last_activity_at = now
        await db.commit()
        await db.refresh(existing)
        return existing
    progress = ProductTourProgress(
        organization_id=payload.organization_id,
        person_id=identity.person_id,
        tour_key=str(tour["key"]),
        surface=payload.surface or str(tour["surface"]),
        role=payload.role,
        current_step_key=first_step,
        last_activity_at=now,
    )
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


async def update_product_tour_step(
    db: AsyncSession,
    identity: CurrentIdentity,
    progress_id: UUID,
    payload: ProductTourStepUpdate,
    authz: AuthorizationService,
) -> ProductTourProgress:
    progress = await get_product_tour_progress(db, progress_id)
    await ensure_manage_training(authz, identity, progress.organization_id)
    tour = product_tour(progress.tour_key)
    step = product_tour_step(tour, payload.step_key)
    completed = decode_string_list(progress.completed_steps_json)
    skipped = decode_string_list(progress.skipped_steps_json)
    if payload.skipped:
        skipped = append_unique(skipped, str(step["key"]))
    else:
        completed = append_unique(completed, str(step["key"]))
        progress.score += int(step["xp"])
    progress.completed_steps_json = json.dumps(completed)
    progress.skipped_steps_json = json.dumps(skipped)
    progress.last_feedback = payload.feedback
    progress.last_activity_at = datetime.now(UTC)
    steps = [str(item["key"]) for item in tour["steps"]]
    done = set(completed) | set(skipped)
    remaining = [key for key in steps if key not in done]
    progress.current_step_key = remaining[0] if remaining else None
    progress.star_count = product_tour_star_count(progress.score, len(completed), len(steps))
    if not remaining:
        progress.status = "completed"
        progress.completed_at = progress.last_activity_at
    else:
        progress.status = "active"
    await db.commit()
    await db.refresh(progress)
    return progress


async def list_product_tour_progress(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> list[ProductTourProgress]:
    await ensure_manage_training(authz, identity, organization_id)
    return list(
        (
            await db.scalars(
                select(ProductTourProgress)
                .where(ProductTourProgress.organization_id == organization_id)
                .order_by(ProductTourProgress.last_activity_at.desc().nullslast(), ProductTourProgress.created_at.desc())
            )
        ).all()
    )


async def search_product_help(
    db: AsyncSession,
    identity: CurrentIdentity | None,
    query: str,
    *,
    organization_id: UUID | None = None,
    surface: str | None = None,
    role: str | None = None,
) -> dict[str, object]:
    normalized = query.strip().lower()
    articles = filter_catalog(product_help_articles(), surface, role)
    scored: list[tuple[int, dict[str, object]]] = []
    for item in articles:
        haystack = " ".join(
            [
                str(item["title"]),
                str(item["summary"]),
                str(item["body"]),
                " ".join(str(tag) for tag in item.get("tags", [])),
            ]
        ).lower()
        score = sum(1 for token in normalized.split() if token and token in haystack)
        if not normalized or score:
            scored.append((score, item))
    results = [item for _, item in sorted(scored, key=lambda pair: pair[0], reverse=True)[:8]]
    recommended_keys = {str(item.get("related_tour_key")) for item in results if item.get("related_tour_key")}
    recommended_tours = [
        tour for tour in product_tour_catalog() if str(tour["key"]) in recommended_keys
    ] or filter_catalog(product_tour_catalog(), surface, role)[:2]
    if identity is not None:
        db.add(
            ProductHelpInteraction(
                organization_id=organization_id,
                person_id=identity.person_id,
                surface=surface,
                role=role,
                query=query.strip(),
                result_count=len(results),
                selected_article_key=str(results[0]["key"]) if results else None,
            )
        )
        await db.commit()
    return {
        "query": query,
        "surface": surface,
        "role": role,
        "result_count": len(results),
        "articles": results,
        "recommended_tours": recommended_tours,
        "suggested_actions": help_suggested_actions(results, recommended_tours),
    }


async def product_experience_dashboard(
    db: AsyncSession,
    identity: CurrentIdentity,
    organization_id: UUID,
    authz: AuthorizationService,
) -> dict[str, object]:
    progress = await list_product_tour_progress(db, identity, organization_id, authz)
    progress_reads = [await product_tour_progress_read(db, item) for item in progress]
    completed = [item for item in progress_reads if item["status"] == "completed"]
    recent_searches = list(
        (
            await db.scalars(
                select(ProductHelpInteraction)
                .where(ProductHelpInteraction.organization_id == organization_id)
                .order_by(ProductHelpInteraction.created_at.desc())
                .limit(5)
            )
        ).all()
    )
    recommended = [
        tour for tour in product_tour_catalog()
        if str(tour["key"]) not in {str(item["tour_key"]) for item in progress_reads if item["status"] == "completed"}
    ][:4]
    return {
        "organization_id": organization_id,
        "active_tour_count": len([item for item in progress_reads if item["status"] == "active"]),
        "completed_tour_count": len(completed),
        "average_progress_percent": round(
            sum(int(item["progress_percent"]) for item in progress_reads) / len(progress_reads)
        ) if progress_reads else 0,
        "total_score": sum(int(item["score"]) for item in progress_reads),
        "active_progress": progress_reads,
        "recent_searches": [
            {
                "query": item.query,
                "surface": item.surface,
                "result_count": item.result_count,
                "selected_article_key": item.selected_article_key,
                "created_at": item.created_at.isoformat(),
            }
            for item in recent_searches
        ],
        "recommended_tours": recommended,
        "suggested_actions": experience_suggested_actions(progress_reads, recommended),
    }


async def product_tour_progress_read(db: AsyncSession, progress: ProductTourProgress) -> dict[str, object]:
    person = await db.get(Person, progress.person_id)
    tour = product_tour(progress.tour_key)
    completed = decode_string_list(progress.completed_steps_json)
    skipped = decode_string_list(progress.skipped_steps_json)
    steps = [dict(step) for step in tour["steps"]]
    current_step = next((step for step in steps if step["key"] == progress.current_step_key), None)
    done_count = len(set(completed) | set(skipped))
    return {
        "id": progress.id,
        "organization_id": progress.organization_id,
        "person_id": progress.person_id,
        "person_name": person.display_name if person else "Unknown user",
        "tour_key": progress.tour_key,
        "surface": progress.surface,
        "role": progress.role,
        "title": str(tour["title"]),
        "current_step_key": progress.current_step_key,
        "current_step": current_step,
        "completed_steps": completed,
        "skipped_steps": skipped,
        "progress_percent": round(done_count / len(steps) * 100) if steps else 100,
        "score": progress.score,
        "star_count": progress.star_count,
        "status": progress.status,
        "last_feedback": progress.last_feedback,
        "completed_at": progress.completed_at,
        "last_activity_at": progress.last_activity_at,
        "created_at": progress.created_at,
    }


async def get_product_tour_progress(db: AsyncSession, progress_id: UUID) -> ProductTourProgress:
    progress = await db.get(ProductTourProgress, progress_id)
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product tour progress not found")
    return progress


async def get_organization(db: AsyncSession, organization_id: UUID) -> Organization:
    organization = await db.get(Organization, organization_id)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


def filter_catalog(items: list[dict[str, object]], surface: str | None, role: str | None) -> list[dict[str, object]]:
    return [
        item
        for item in items
        if (surface is None or item.get("surface") == surface)
        and (role is None or item.get("role") in {role, "all"})
    ]


def product_tour(tour_key: str) -> dict[str, object]:
    for tour in product_tour_catalog():
        if tour["key"] == tour_key:
            return tour
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown product tour")


def product_tour_step(tour: dict[str, object], step_key: str) -> dict[str, object]:
    for step in tour.get("steps", []):
        if isinstance(step, dict) and step.get("key") == step_key:
            return step
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unknown product tour step")


def product_tour_star_count(score: int, completed_count: int, total_steps: int) -> int:
    if total_steps <= 0:
        return 3
    completion_ratio = completed_count / total_steps
    if completion_ratio >= 1 and score >= total_steps * 45:
        return 3
    if completion_ratio >= 0.66:
        return 2
    if completion_ratio > 0:
        return 1
    return 0


def decode_string_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item)]


def append_unique(values: list[str], value: str) -> list[str]:
    return list(dict.fromkeys([*values, value]))


def help_suggested_actions(
    articles: list[dict[str, object]],
    tours: list[dict[str, object]],
) -> list[str]:
    actions = [str(item["action_label"]) for item in articles if item.get("action_label")]
    actions.extend(f"Start tour: {tour['title']}" for tour in tours[:2])
    return list(dict.fromkeys(actions))[:5]


def experience_suggested_actions(progress: list[dict[str, object]], recommended: list[dict[str, object]]) -> list[str]:
    actions: list[str] = []
    active = [item for item in progress if item["status"] == "active" and item.get("current_step")]
    if active:
        step = active[0]["current_step"]
        if isinstance(step, dict):
            actions.append(f"Resume {active[0]['title']}: {step['practice_task']}")
    if recommended:
        actions.append(f"Start {recommended[0]['title']} for the next guided workflow.")
    actions.append("Use contextual help search before handing a workflow to a new staff member.")
    return list(dict.fromkeys(actions))
