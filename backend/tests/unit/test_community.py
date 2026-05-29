def create_community_context(client, identity_headers):
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Community Club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()
    team = client.post(
        "/api/v1/teams",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Community U16",
            "sport": "football",
            "sport_format": "team",
        },
    ).json()
    return organization, team


def test_community_posts_comments_reactions_polls_votes_and_summary(client, identity_headers) -> None:
    organization, team = create_community_context(client, identity_headers)

    post = client.post(
        "/api/v1/community/posts",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "title": "Matchday moments",
            "body": "Share goals, photos, and supporter notes from the weekend.",
            "post_type": "matchday",
            "visibility": "public",
            "media_url": "https://media.example/matchday.jpg",
            "pinned": True,
        },
    ).json()
    assert post["title"] == "Matchday moments"
    assert post["author_person_id"] is not None
    assert post["pinned"] is True

    comment = client.post(
        f"/api/v1/community/posts/{post['id']}/comments",
        headers=identity_headers,
        json={"body": "Great midfield pressure and strong family support."},
    ).json()
    assert comment["post_id"] == post["id"]
    assert comment["status"] == "published"

    flagged_comment = client.post(
        f"/api/v1/community/posts/{post['id']}/comments",
        headers=identity_headers,
        json={"body": "This looks like a scam threat with abuse and too many bad links https://a.example https://b.example https://c.example"},
    ).json()
    assert flagged_comment["status"] == "needs_review"

    moderation_queue = client.get(
        f"/api/v1/community/moderation-queue?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert moderation_queue["review_count"] == 1
    assert moderation_queue["items"][0]["item_type"] == "comment"
    assert moderation_queue["items"][0]["risk_score"] >= 35

    moderated_comment = client.post(
        f"/api/v1/community/comments/{flagged_comment['id']}/moderation",
        headers=identity_headers,
        json={"status": "hidden", "note": "Spam and abuse risk."},
    ).json()
    assert moderated_comment["status"] == "hidden"

    hidden_queue = client.get(
        f"/api/v1/community/moderation-queue?organization_id={organization['id']}",
        headers=identity_headers,
    ).json()
    assert hidden_queue["hidden_count"] == 1

    share_package = client.post(
        f"/api/v1/community/posts/{post['id']}/social-share?base_url=https://club.example",
        headers=identity_headers,
    ).json()
    assert share_package["public_url"].startswith("https://club.example/site/")
    assert {channel["channel"] for channel in share_package["channels"]} >= {"whatsapp", "facebook", "x"}
    assert share_package["risk_score"] == 0

    reaction = client.post(
        f"/api/v1/community/posts/{post['id']}/reactions",
        headers=identity_headers,
        json={"reaction_type": "celebrate"},
    ).json()
    assert reaction["reaction_type"] == "celebrate"

    duplicate_reaction = client.post(
        f"/api/v1/community/posts/{post['id']}/reactions",
        headers=identity_headers,
        json={"reaction_type": "celebrate"},
    ).json()
    assert duplicate_reaction["id"] == reaction["id"]

    poll = client.post(
        "/api/v1/community/polls",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "team_id": team["id"],
            "post_id": post["id"],
            "question": "Who was player of the match?",
            "audience": "supporters",
            "options": [
                {"label": "Amina"},
                {"label": "Brian"},
                {"label": "Team defence"},
            ],
        },
    ).json()
    assert poll["question"] == "Who was player of the match?"
    assert poll["total_votes"] == 0
    assert [option["sequence"] for option in poll["options"]] == [1, 2, 3]

    vote = client.post(
        f"/api/v1/community/polls/{poll['id']}/votes",
        headers=identity_headers,
        json={"option_id": poll["options"][0]["id"]},
    ).json()
    assert vote["option_id"] == poll["options"][0]["id"]

    updated_vote = client.post(
        f"/api/v1/community/polls/{poll['id']}/votes",
        headers=identity_headers,
        json={"option_id": poll["options"][1]["id"]},
    ).json()
    assert updated_vote["id"] == vote["id"]
    assert updated_vote["option_id"] == poll["options"][1]["id"]

    posts = client.get(
        f"/api/v1/community/posts?organization_id={organization['id']}&team_id={team['id']}"
    ).json()
    assert posts[0]["comment_count"] == 2
    assert posts[0]["reaction_count"] == 1
    assert posts[0]["poll_count"] == 1

    comments = client.get(f"/api/v1/community/posts/{post['id']}/comments").json()
    assert [item["status"] for item in comments] == ["published", "hidden"]

    polls = client.get(
        f"/api/v1/community/polls?organization_id={organization['id']}&team_id={team['id']}"
    ).json()
    assert polls[0]["total_votes"] == 1
    assert {option["label"]: option["vote_count"] for option in polls[0]["options"]} == {
        "Amina": 0,
        "Brian": 1,
        "Team defence": 0,
    }

    summary = client.get(f"/api/v1/community/summary?organization_id={organization['id']}").json()
    assert summary["post_count"] == 1
    assert summary["pinned_post_count"] == 1
    assert summary["comment_count"] == 2
    assert summary["reaction_count"] == 1
    assert summary["poll_count"] == 1
    assert summary["open_poll_count"] == 1
    assert summary["vote_count"] == 1
    assert summary["engagement_score"] > 0
    assert summary["recommendations"]


def test_supporter_memberships_alumni_profiles_and_mentorship(client, identity_headers) -> None:
    organization, _team = create_community_context(client, identity_headers)

    tier = client.post(
        "/api/v1/community/supporter-tiers",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "VIP Season Holder",
            "slug": "vip-season-holder",
            "monthly_price": "20.00",
            "currency": "USD",
            "benefits": "Behind-the-scenes content, major votes, meet-and-greet access.",
            "voting_weight": 5,
            "trial_days": 14,
        },
    ).json()
    assert tier["status"] == "active"
    assert tier["voting_weight"] == 5

    supporter = client.post(
        "/api/v1/community/supporters",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "tier_id": tier["id"],
            "display_name": "Sarah Supporter",
            "email": "sarah.supporter@example.com",
            "lifetime_value": "60.00",
            "notes": "Family package candidate and matchday volunteer.",
        },
    ).json()
    assert supporter["tier_name"] == "VIP Season Holder"
    assert supporter["engagement_points"] == 0

    activity = client.post(
        f"/api/v1/community/supporters/{supporter['id']}/activities",
        headers=identity_headers,
        json={
            "activity_type": "match_attendance",
            "source": "ticketing",
            "description": "Attended derby and voted in player-of-the-match poll.",
            "points": 1250,
            "value_amount": "15.00",
        },
    ).json()
    assert activity["points"] == 1250
    assert activity["source"] == "ticketing"

    reward = client.post(
        f"/api/v1/community/supporters/{supporter['id']}/rewards",
        headers=identity_headers,
        json={
            "title": "Meet and greet ticket",
            "reward_type": "experience",
            "threshold_points": 1000,
        },
    ).json()
    assert reward["status"] == "earned"

    redeemed_reward = client.post(
        f"/api/v1/community/supporter-rewards/{reward['id']}/redeem",
        headers=identity_headers,
    ).json()
    assert redeemed_reward["status"] == "redeemed"
    assert redeemed_reward["redeemed_at"] is not None

    challenge = client.post(
        "/api/v1/community/fan-challenges",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "title": "Derby week superfan",
            "description": "Attend, vote, comment, and share during derby week.",
            "challenge_type": "matchday",
            "target_activity_type": "match_attendance",
            "target_count": 2,
            "points_reward": 750,
            "badge_name": "Derby Superfan",
            "starts_at": "2026-06-01T00:00:00Z",
            "ends_at": "2026-06-08T00:00:00Z",
        },
    ).json()
    assert challenge["status"] == "active"
    assert challenge["completion_count"] == 0

    in_progress = client.post(
        f"/api/v1/community/fan-challenges/{challenge['id']}/progress",
        headers=identity_headers,
        json={"supporter_profile_id": supporter["id"], "progress_count": 1},
    ).json()
    assert in_progress["status"] == "in_progress"
    assert in_progress["points_awarded"] == 0

    completed = client.post(
        f"/api/v1/community/fan-challenges/{challenge['id']}/progress",
        headers=identity_headers,
        json={"supporter_profile_id": supporter["id"], "progress_count": 1},
    ).json()
    assert completed["status"] == "completed"
    assert completed["points_awarded"] == 750
    assert completed["completed_at"] is not None

    challenges = client.get(
        f"/api/v1/community/fan-challenges?organization_id={organization['id']}"
    ).json()
    assert challenges[0]["completion_count"] == 1

    supporters = client.get(f"/api/v1/community/supporters?organization_id={organization['id']}").json()
    assert supporters[0]["engagement_points"] == 2000
    assert supporters[0]["lifetime_value"] == "75.00"

    leaderboard = client.get(
        f"/api/v1/community/fan-leaderboard?organization_id={organization['id']}&limit=5"
    ).json()
    assert leaderboard[0]["rank"] == 1
    assert leaderboard[0]["supporter_name"] == "Sarah Supporter"
    assert leaderboard[0]["engagement_points"] == 2000
    assert leaderboard[0]["reward_count"] >= 2
    assert leaderboard[0]["completed_challenge_count"] == 1

    supporter_dashboard = client.get(
        f"/api/v1/community/supporter-dashboard?organization_id={organization['id']}"
    ).json()
    assert supporter_dashboard["tier_count"] == 1
    assert supporter_dashboard["supporter_count"] == 1
    assert supporter_dashboard["total_points"] == 2000
    assert supporter_dashboard["top_supporter_name"] == "Sarah Supporter"
    assert supporter_dashboard["reward_count"] >= 2
    assert supporter_dashboard["challenge_count"] == 1
    assert supporter_dashboard["completed_challenge_count"] == 1

    alumni = client.post(
        "/api/v1/community/alumni",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "display_name": "Michael Mentor",
            "email": "michael.mentor@example.com",
            "graduation_year": 2018,
            "sports_history": "Community Club U8 to U18, college captain, youth coach.",
            "career_industry": "Sports Management",
            "current_company": "Community Club",
            "current_role": "Head of Youth Development",
            "linkedin_url": "https://linkedin.example/michael",
            "engagement_level": "active",
            "lifetime_donations": "5200.00",
            "privacy_status": "network_visible",
        },
    ).json()
    assert alumni["career_industry"] == "Sports Management"

    program = client.post(
        "/api/v1/community/mentorship-programs",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "name": "Future Leaders",
            "goals": "Career guidance, professional networking, and life-after-sport planning.",
            "industry_focus": "Sports Management",
            "capacity": 40,
            "starts_on": "2026-06-01",
            "ends_on": "2026-12-15",
        },
    ).json()
    assert program["match_count"] == 0

    match = client.post(
        f"/api/v1/community/mentorship-programs/{program['id']}/matches",
        headers=identity_headers,
        json={
            "alumni_profile_id": alumni["id"],
            "mentee_name": "Emma Johnson",
            "mentee_interest": "Sports Management",
            "goals": "Explore coaching, sports operations, and college pathway decisions.",
            "next_meeting_at": "2026-06-10T15:00:00Z",
        },
    ).json()
    assert match["alumni_name"] == "Michael Mentor"
    assert match["match_score"] >= 90

    programs = client.get(
        f"/api/v1/community/mentorship-programs?organization_id={organization['id']}"
    ).json()
    assert programs[0]["match_count"] == 1

    matches = client.get(
        f"/api/v1/community/mentorship-matches?organization_id={organization['id']}"
    ).json()
    assert matches[0]["mentee_name"] == "Emma Johnson"

    alumni_dashboard = client.get(
        f"/api/v1/community/alumni-dashboard?organization_id={organization['id']}"
    ).json()
    assert alumni_dashboard["alumni_count"] == 1
    assert alumni_dashboard["active_alumni_count"] == 1
    assert alumni_dashboard["mentorship_program_count"] == 1
    assert alumni_dashboard["mentorship_match_count"] == 1
    assert alumni_dashboard["mentor_capacity"] == 40
    assert alumni_dashboard["lifetime_donations"] == "5200.00"
