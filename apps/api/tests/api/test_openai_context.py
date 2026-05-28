from app.services.openai_inbox import _instructions


def test_openai_inbox_instructions_require_relative_date_resolution() -> None:
    instructions = _instructions()

    assert "Resolve relative dates" in instructions
    assert "do_window_start" in instructions
    assert "duplicates an existing active or planned task" in instructions
