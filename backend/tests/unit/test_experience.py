def test_product_tours_and_contextual_help_save_progress(client, identity_headers) -> None:
    organization = client.post(
        "/api/v1/organizations",
        headers=identity_headers,
        json={
            "name": "Guided Experience Club",
            "slug": "guided-experience-club",
            "organization_type": "club",
            "primary_sport": "football",
        },
    ).json()

    catalog_response = client.get("/api/v1/experience/catalog?surface=performance&role=coach")
    assert catalog_response.status_code == 200
    catalog = catalog_response.json()
    assert catalog["tours"][0]["key"] == "video_analysis_tour"
    assert catalog["tours"][0]["steps"][0]["key"] == "upload_video"
    assert any(article["key"] == "match_tracking_quality" for article in catalog["articles"])

    start_response = client.post(
        "/api/v1/experience/tours/progress",
        headers=identity_headers,
        json={
            "organization_id": organization["id"],
            "tour_key": "video_analysis_tour",
            "surface": "performance",
            "role": "coach",
        },
    )
    assert start_response.status_code == 201
    progress = start_response.json()
    assert progress["person_name"] == "Owner Example"
    assert progress["current_step_key"] == "upload_video"
    assert progress["progress_percent"] == 0

    first_step = client.post(
        f"/api/v1/experience/tours/progress/{progress['id']}/steps",
        headers=identity_headers,
        json={"step_key": "upload_video", "feedback": "Demo clip uploaded."},
    )
    assert first_step.status_code == 200
    progress = first_step.json()
    assert progress["completed_steps"] == ["upload_video"]
    assert progress["score"] == 40
    assert progress["current_step_key"] == "tag_players"

    skip_step = client.post(
        f"/api/v1/experience/tours/progress/{progress['id']}/steps",
        headers=identity_headers,
        json={"step_key": "tag_players", "skipped": True, "feedback": "Return after identity review."},
    )
    assert skip_step.status_code == 200
    progress = skip_step.json()
    assert progress["skipped_steps"] == ["tag_players"]
    assert progress["status"] == "active"

    for step_key in ["choose_metrics", "review_guidance"]:
        complete = client.post(
            f"/api/v1/experience/tours/progress/{progress['id']}/steps",
            headers=identity_headers,
            json={"step_key": step_key},
        )
        assert complete.status_code == 200
        progress = complete.json()

    assert progress["status"] == "completed"
    assert progress["progress_percent"] == 100
    assert progress["completed_at"] is not None
    assert progress["star_count"] >= 2

    search_response = client.get(
        f"/api/v1/experience/help/search?organization_id={organization['id']}&surface=performance&role=coach&q=tracking%20distance%20quality",
        headers=identity_headers,
    )
    assert search_response.status_code == 200
    search = search_response.json()
    assert search["result_count"] >= 1
    assert search["articles"][0]["key"] == "match_tracking_quality"
    assert search["recommended_tours"][0]["key"] == "video_analysis_tour"

    dashboard_response = client.get(
        f"/api/v1/experience/dashboard?organization_id={organization['id']}",
        headers=identity_headers,
    )
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["completed_tour_count"] == 1
    assert dashboard["total_score"] == progress["score"]
    assert dashboard["recent_searches"][0]["query"] == "tracking distance quality"
    assert any("contextual help" in action.lower() for action in dashboard["suggested_actions"])
