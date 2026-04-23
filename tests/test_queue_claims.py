from datetime import datetime, timedelta, timezone

from computer_use_toolkit.queue.claims import claim_pending_action, report_pending_action_result



def _session(*, pending_action, claim_token="", virtual_cursor=None, last_result="sentinel"):
    return {
        "app_session_id": "app-1",
        "pending_pointer_action": pending_action,
        "pending_pointer_claim_token": claim_token,
        "virtual_cursor": virtual_cursor or {"x": 1, "y": 2},
        "last_pointer_action_result": last_result,
    }



def test_claim_pending_action_sets_claim_metadata_and_token_without_mutating_input():
    now = datetime(2026, 4, 23, 15, 30, tzinfo=timezone.utc)
    session = _session(pending_action={"action_id": "ptr-1", "action_type": "click", "x": 10, "y": 20})

    result = claim_pending_action(
        session,
        action_id="ptr-1",
        worker_id="worker-1",
        now=now,
        claim_ttl_seconds=30,
        claim_token_factory=lambda: "claim-1",
    )

    assert result["success"] is True
    assert result["claim_token"] == "claim-1"
    assert result["reason"] == "claimed"
    assert result["session"]["pending_pointer_action"]["claimed_by"] == "worker-1"
    assert result["session"]["pending_pointer_action"]["claimed_at"] == now.isoformat()
    assert result["session"]["pending_pointer_action"]["claim_expires_at"] == (now + timedelta(seconds=30)).isoformat()
    assert result["session"]["pending_pointer_claim_token"] == "claim-1"
    assert result["session"]["last_pointer_action_result"] is None
    assert "claimed_by" not in session["pending_pointer_action"]
    assert session["pending_pointer_claim_token"] == ""
    assert session["last_pointer_action_result"] == "sentinel"



def test_claim_pending_action_rejects_already_claimed_pending_action():
    now = datetime(2026, 4, 23, 15, 30, tzinfo=timezone.utc)
    session = _session(
        pending_action={
            "action_id": "ptr-1",
            "action_type": "click",
            "claimed_by": "worker-0",
            "claim_expires_at": (now + timedelta(seconds=30)).isoformat(),
        },
        claim_token="claim-existing",
    )

    result = claim_pending_action(
        session,
        action_id="ptr-1",
        worker_id="worker-1",
        now=now,
        claim_ttl_seconds=30,
        claim_token_factory=lambda: "claim-new",
    )

    assert result == {
        "success": False,
        "reason": "action_claimed",
        "claimed_by": "worker-0",
        "session": session,
    }



def test_claim_pending_action_treats_malformed_claim_expiry_as_still_claimed():
    now = datetime(2026, 4, 23, 15, 30, tzinfo=timezone.utc)
    session = _session(
        pending_action={
            "action_id": "ptr-1",
            "action_type": "click",
            "claimed_by": "worker-0",
            "claim_expires_at": "not-a-timestamp",
        },
        claim_token="claim-existing",
    )

    result = claim_pending_action(
        session,
        action_id="ptr-1",
        worker_id="worker-1",
        now=now,
        claim_ttl_seconds=30,
        claim_token_factory=lambda: "claim-new",
    )

    assert result == {
        "success": False,
        "reason": "action_claimed",
        "claimed_by": "worker-0",
        "session": session,
    }



def test_report_pending_action_result_rejects_expired_claim():
    now = datetime(2026, 4, 23, 15, 30, tzinfo=timezone.utc)
    session = _session(
        pending_action={
            "action_id": "ptr-1",
            "action_type": "click",
            "claimed_by": "worker-1",
            "claim_expires_at": (now - timedelta(seconds=1)).isoformat(),
        },
        claim_token="claim-1",
    )

    result = report_pending_action_result(
        session,
        action_id="ptr-1",
        status="completed",
        claim_token="claim-1",
        now=now,
    )

    assert result == {
        "success": False,
        "reason": "claim_expired",
        "claimed_by": "worker-1",
        "session": session,
    }



def test_report_pending_action_result_clears_pending_and_records_result():
    now = datetime(2026, 4, 23, 15, 30, tzinfo=timezone.utc)
    session = _session(
        pending_action={
            "action_id": "ptr-1",
            "action_type": "scroll",
            "delta_y": -120,
            "claimed_by": "worker-1",
            "claim_expires_at": (now + timedelta(seconds=30)).isoformat(),
        },
        claim_token="claim-1",
        virtual_cursor={"x": 1, "y": 2},
    )

    result = report_pending_action_result(
        session,
        action_id="ptr-1",
        status="completed",
        claim_token="claim-1",
        now=now,
        x=40,
        y=50,
    )

    assert result["success"] is True
    assert result["reason"] == "reported"
    assert result["status"] == "completed"
    assert result["result"]["action_id"] == "ptr-1"
    assert result["result"]["action_type"] == "scroll"
    assert result["result"]["delta_y"] == -120
    assert result["result"]["status"] == "completed"
    assert result["result"]["reported_by"] == "worker-1"
    assert result["result"]["x"] == 40
    assert result["result"]["y"] == 50
    assert result["session"]["pending_pointer_action"] is None
    assert result["session"]["pending_pointer_claim_token"] == ""
    assert result["session"]["last_pointer_action_result"] == result["result"]
    assert result["session"]["virtual_cursor"] == {
        "x": 40,
        "y": 50,
        "detached": True,
        "visible": True,
    }
    assert session["pending_pointer_action"]["action_id"] == "ptr-1"
    assert session["pending_pointer_claim_token"] == "claim-1"
    assert session["virtual_cursor"] == {"x": 1, "y": 2}



def test_report_pending_action_result_allows_direct_report_for_unclaimed_action_source_parity():
    now = datetime(2026, 4, 23, 15, 30, tzinfo=timezone.utc)
    session = _session(
        pending_action={
            "action_id": "ptr-1",
            "action_type": "click",
            "x": 10,
            "y": 20,
        },
        claim_token="",
        virtual_cursor={"x": 1, "y": 2},
    )

    result = report_pending_action_result(
        session,
        action_id="ptr-1",
        status="completed",
        claim_token=None,
        now=now,
        x=10,
        y=20,
    )

    assert result["success"] is True
    assert result["reason"] == "reported"
    assert result["result"]["status"] == "completed"
    assert "reported_by" not in result["result"]
    assert result["session"]["pending_pointer_action"] is None



def test_report_pending_action_result_allows_matching_token_when_claim_expiry_is_missing_source_parity():
    now = datetime(2026, 4, 23, 15, 30, tzinfo=timezone.utc)
    session = _session(
        pending_action={
            "action_id": "ptr-1",
            "action_type": "click",
            "claimed_by": "worker-1",
            "claimed_at": now.isoformat(),
        },
        claim_token="claim-1",
    )

    result = report_pending_action_result(
        session,
        action_id="ptr-1",
        status="completed",
        claim_token="claim-1",
        now=now,
    )

    assert result["success"] is True
    assert result["reason"] == "reported"
    assert result["result"]["reported_by"] == "worker-1"



def test_report_pending_action_result_rehydrates_missing_virtual_cursor_flags_source_parity():
    now = datetime(2026, 4, 23, 15, 30, tzinfo=timezone.utc)
    session = _session(
        pending_action={
            "action_id": "ptr-1",
            "action_type": "click",
            "claimed_by": "worker-1",
            "claim_expires_at": (now + timedelta(seconds=30)).isoformat(),
        },
        claim_token="claim-1",
    )
    session["virtual_cursor"] = None

    result = report_pending_action_result(
        session,
        action_id="ptr-1",
        status="completed",
        claim_token="claim-1",
        now=now,
        x=15,
        y=25,
    )

    assert result["success"] is True
    assert result["session"]["virtual_cursor"] == {
        "x": 15,
        "y": 25,
        "detached": True,
        "visible": True,
    }



def test_report_pending_action_result_rehydrates_partial_virtual_cursor_shape_source_parity():
    now = datetime(2026, 4, 23, 15, 30, tzinfo=timezone.utc)
    session = _session(
        pending_action={
            "action_id": "ptr-1",
            "action_type": "click",
            "claimed_by": "worker-1",
            "claim_expires_at": (now + timedelta(seconds=30)).isoformat(),
        },
        claim_token="claim-1",
        virtual_cursor={},
    )

    result = report_pending_action_result(
        session,
        action_id="ptr-1",
        status="completed",
        claim_token="claim-1",
        now=now,
        x=15,
        y=25,
    )

    assert result["success"] is True
    assert result["session"]["virtual_cursor"] == {
        "x": 15,
        "y": 25,
        "detached": True,
        "visible": True,
    }
