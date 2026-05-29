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
    assert posts[0]["comment_count"] == 1
    assert posts[0]["reaction_count"] == 1
    assert posts[0]["poll_count"] == 1

    comments = client.get(f"/api/v1/community/posts/{post['id']}/comments").json()
    assert [item["body"] for item in comments] == ["Great midfield pressure and strong family support."]

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
    assert summary["comment_count"] == 1
    assert summary["reaction_count"] == 1
    assert summary["poll_count"] == 1
    assert summary["open_poll_count"] == 1
    assert summary["vote_count"] == 1
    assert summary["engagement_score"] > 0
    assert summary["recommendations"]
