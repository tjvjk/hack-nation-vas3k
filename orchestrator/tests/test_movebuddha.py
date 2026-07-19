from app.movebuddha import MoveBuddhaClient


def test_extracts_professional_range_for_selected_move_size():
    result = MoveBuddhaClient._professional_estimate(
        {
            "sizes": {
                "two_bedrooms": {
                    "professional": {"min": 817, "max": 1926},
                }
            }
        },
        "two_bedrooms",
    )

    assert result == {"low": 817.0, "high": 1926.0}


def test_rejects_malformed_professional_range():
    assert MoveBuddhaClient._professional_estimate({"sizes": {"two_bedrooms": {"professional": {"min": 900}}}}, "two_bedrooms") is None
