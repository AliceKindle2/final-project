"""
test_logic_utils.py — pytest suite for Glitchy Guesser

Run with:  pytest test_logic_utils.py -v

Covers:
  1. parse_guess      — valid input, empty input, non-numeric input
  2. check_guess      — win, too high, too low
  3. update_score     — win scaling, floor at zero, no reward for misses
  4. AgentOpponent    — always solves within max_guesses (full range)
  5. AgentOpponent    — edge case: secret is the lowest boundary value (1)
  6. AgentOpponent    — edge case: secret is the highest boundary value (100)
"""

import pytest
from logic_utils import (
    parse_guess,
    check_guess,
    update_score,
    AgentOpponent,
)


# ── Helper: run agent to completion against a known secret ──────────────────

def run_agent_to_completion(low: int, high: int, secret: int):
    """Drive the full plan → act → reflect loop until solved or bust."""
    agent = AgentOpponent(low, high)
    for _ in range(agent.max_guesses + 5):   # +5 buffer to detect overrun
        guess, _ = agent.plan_and_act()
        outcome, _ = check_guess(guess, secret)
        agent.reflect(outcome)
        if agent.solved:
            break
    return agent


# ────────────────────────────────────────────────────────────────────────────
# Test 1 — parse_guess: valid, empty, and non-numeric inputs
# ────────────────────────────────────────────────────────────────────────────

def test_parse_guess_handles_all_input_types():
    """parse_guess must accept valid ints/floats and reject bad input cleanly."""

    # plain integer string
    ok, value, err = parse_guess("42")
    assert ok is True
    assert value == 42
    assert err is None

    # decimal string — should truncate to int, not error
    ok, value, err = parse_guess("42.9")
    assert ok is True
    assert value == 42

    # empty string — common user mistake
    ok, value, err = parse_guess("")
    assert ok is False
    assert value is None
    assert err == "Enter a guess."

    # None — defensive check if text_input returns None
    ok, value, err = parse_guess(None)
    assert ok is False
    assert err == "Enter a guess."

    # letters — should fail gracefully with a message
    ok, value, err = parse_guess("abc")
    assert ok is False
    assert err == "That is not a number."

    # mixed — e.g. user typed units like "50px"
    ok, value, err = parse_guess("50px")
    assert ok is False
    assert err == "That is not a number."


# ────────────────────────────────────────────────────────────────────────────
# Test 2 — check_guess: all three outcomes
# ────────────────────────────────────────────────────────────────────────────

def test_check_guess_returns_correct_outcomes():
    """check_guess must return Win, Too High, or Too Low correctly."""
    outcome, msg = check_guess(50, 50)
    assert outcome == "Win"
    assert "Correct" in msg

    outcome, msg = check_guess(80, 50)
    assert outcome == "Too High"
    assert "LOWER" in msg

    outcome, msg = check_guess(20, 50)
    assert outcome == "Too Low"
    assert "HIGHER" in msg

    # secret passed as string (Streamlit session state can do this)
    outcome, _ = check_guess(50, "50")
    assert outcome == "Win"


# ────────────────────────────────────────────────────────────────────────────
# Test 3 — update_score: win scaling, miss penalty, floor at zero
# ────────────────────────────────────────────────────────────────────────────

def test_update_score_win_scales_and_misses_never_go_negative():
    """Score must scale down with attempts, floor at 0, never reward misses."""

    # First-guess win: 100 - 10*(1-1) = 100 points
    score = update_score(0, "Win", attempt_number=1)
    assert score == 100

    # Late win: 100 - 10*(9-1) = 20 points
    score = update_score(0, "Win", attempt_number=9)
    assert score == 20

    # Very late win: floors at 10 minimum
    score = update_score(0, "Win", attempt_number=99)
    assert score == 10

    # Miss deducts 5
    score = update_score(20, "Too High", attempt_number=3)
    assert score == 15

    # Miss never drops below 0
    score = update_score(3, "Too Low", attempt_number=1)
    assert score == 0

    # Score stays 0 when already at 0
    score = update_score(0, "Too High", attempt_number=1)
    assert score == 0


# ────────────────────────────────────────────────────────────────────────────
# Test 4 — AgentOpponent: always solves within max_guesses (1–100)
# ────────────────────────────────────────────────────────────────────────────

def test_agent_always_solves_within_max_guesses():
    """
    Binary search must solve every possible secret in range without exceeding
    the theoretical max guesses ceiling. Tests all 100 values exhaustively.
    """
    low, high = 1, 100
    for secret in range(low, high + 1):
        agent = run_agent_to_completion(low, high, secret)
        assert agent.solved, f"Agent failed to solve secret={secret}"
        assert agent.guess_count <= agent.max_guesses, (
            f"Agent used {agent.guess_count} guesses for secret={secret}, "
            f"max allowed={agent.max_guesses}"
        )


# ────────────────────────────────────────────────────────────────────────────
# Test 5 — AgentOpponent edge case: secret is the lowest boundary (1)
# ────────────────────────────────────────────────────────────────────────────

def test_agent_solves_lowest_boundary():
    """
    Secret = 1 forces the agent to repeatedly go lower until it hits the
    floor. This tests that the belief state never goes below low=1
    and that the agent still solves it without an infinite loop.
    """
    agent = run_agent_to_completion(1, 100, secret=1)

    assert agent.solved, "Agent did not solve secret=1"
    assert agent.guess_count <= agent.max_guesses
    # Belief state should never have gone below the original low
    assert agent.low >= 1
    # The log should contain at least one REFLECT entry showing "too high"
    reflect_lines = [l for l in agent.log if "[REFLECT]" in l and "too high" in l.lower()]
    assert len(reflect_lines) > 0, "Expected multiple 'too high' reflections for secret=1"


# ────────────────────────────────────────────────────────────────────────────
# Test 6 — AgentOpponent edge case: secret is the highest boundary (100)
# ────────────────────────────────────────────────────────────────────────────

def test_agent_solves_highest_boundary():
    """
    Secret = 100 forces the agent to repeatedly go higher until it hits the
    ceiling. This tests that the belief state never exceeds high=100
    and that the agent converges correctly from below.
    """
    agent = run_agent_to_completion(1, 100, secret=100)

    assert agent.solved, "Agent did not solve secret=100"
    assert agent.guess_count <= agent.max_guesses
    # Belief state should never have exceeded the original high
    assert agent.high <= 100
    # The log should contain at least one REFLECT entry showing "too low"
    reflect_lines = [l for l in agent.log if "[REFLECT]" in l and "too low" in l.lower()]
    assert len(reflect_lines) > 0, "Expected multiple 'too low' reflections for secret=100"