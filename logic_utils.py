"""
logic_utils.py — core game logic + AgentOpponent (agentic workflow)

AgentOpponent implements a plan → act → reflect loop:
  - Plan:    decide the best guess given its current belief state (low..high)
  - Act:     commit to a guess (binary midpoint)
  - Reflect: update belief state from feedback, log its reasoning
"""

from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# Difficulty helpers
# ---------------------------------------------------------------------------

def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 200   # FIX: was 1–50 with only 5 attempts — harder range makes Hard actually hard
    return 1, 100


def get_attempt_limit(difficulty: str) -> int:
    """Centralised attempt-limit lookup so app.py and logic stay in sync."""
    return {"Easy": 6, "Normal": 8, "Hard": 8}.get(difficulty, 8)


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def parse_guess(raw: str):
    """
    Parse user input into an int guess.
    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if not raw:                          # covers None and ""
        return False, None, "Enter a guess."
    try:
        value = int(float(raw)) if "." in raw else int(raw)
    except Exception:
        return False, None, "That is not a number."
    return True, value, None


# ---------------------------------------------------------------------------
# Game outcome
# ---------------------------------------------------------------------------

def check_guess(guess, secret):
    """Return (outcome_str, hint_message)."""
    try:
        secret = int(secret)
    except (ValueError, TypeError):
        pass

    if guess == secret:
        return "Win", "🎉 Correct!"
    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


# ---------------------------------------------------------------------------
# Scoring  (FIX: removed the "+5 on even wrong guesses" reward for bad play)
# ---------------------------------------------------------------------------

def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    """
    Win  → +points scaled by how quickly the player guessed
    Miss → -5 per wrong guess (no accidental rewards)
    """
    if outcome == "Win":
        points = max(10, 100 - 10 * (attempt_number - 1))   # FIX: was attempt_number+1 (off-by-one)
        return current_score + points
    # Too High or Too Low
    return max(0, current_score - 5)                         # FIX: floor at 0, no reward for misses


# ---------------------------------------------------------------------------
# Agentic Opponent  ← NEW
# ---------------------------------------------------------------------------

class AgentOpponent:
    """
    An AI opponent that plays the guessing game alongside the human.

    Agentic loop every turn
    ──────────────────────
    1. PLAN    – reason about the remaining search space
    2. ACT     – commit to a guess (binary midpoint = optimal strategy)
    3. REFLECT – update belief state from outcome; log reasoning chain

    Public API
    ──────────
    agent = AgentOpponent(low=1, high=100)
    guess, reasoning = agent.plan_and_act()          # call each turn
    agent.reflect(outcome)                            # "Too High" | "Too Low" | "Win"
    agent.log          → list[str]  full reasoning chain
    agent.solved       → bool
    agent.guess_count  → int
    agent.max_guesses  → int  (theoretical ceiling = ceil(log2(range)))
    """

    def __init__(self, low: int, high: int):
        self._orig_low = low
        self._orig_high = high
        self.low = low
        self.high = high
        self.last_guess: int | None = None
        self.guess_count: int = 0
        self.solved: bool = False
        self.log: list[str] = []
        self.max_guesses: int = math.ceil(math.log2(high - low + 1)) + 1
        self._append(
            f"[INIT] Strategy: binary search over [{low}, {high}]. "
            f"Max guesses needed: {self.max_guesses}."
        )

    # ── public ──────────────────────────────────────────────────────────────

    def plan_and_act(self) -> tuple[int, str]:
        """
        PLAN + ACT phase.
        Returns (guess, one-line reasoning summary).
        """
        if self.solved:
            return self.last_guess, "Already solved."

        # PLAN: assess search space
        space = self.high - self.low + 1
        plan = (
            f"[PLAN] Search space = {space} values [{self.low}..{self.high}]. "
            f"Midpoint eliminates {space // 2} values. "
            f"Guesses used: {self.guess_count}/{self.max_guesses}."
        )
        self._append(plan)

        # ACT: commit to midpoint
        guess = (self.low + self.high) // 2
        self.last_guess = guess
        self.guess_count += 1
        act = f"[ACT]  Guess #{self.guess_count}: {guess}"
        self._append(act)

        summary = f"Space [{self.low}–{self.high}] → guess {guess}"
        return guess, summary

    def reflect(self, outcome: str) -> str:
        """
        REFLECT phase — update belief state from game feedback.
        outcome: "Win" | "Too High" | "Too Low"
        Returns a one-line reflection string.
        """
        if outcome == "Win":
            self.solved = True
            note = f"[REFLECT] Correct! Solved in {self.guess_count} guess(es)."
        elif outcome == "Too High":
            old_high = self.high
            self.high = self.last_guess - 1
            note = (
                f"[REFLECT] {self.last_guess} is too high. "
                f"Upper bound: {old_high} → {self.high}. "
                f"New space: [{self.low}, {self.high}]."
            )
        elif outcome == "Too Low":
            old_low = self.low
            self.low = self.last_guess + 1
            note = (
                f"[REFLECT] {self.last_guess} is too low. "
                f"Lower bound: {old_low} → {self.low}. "
                f"New space: [{self.low}, {self.high}]."
            )
        else:
            note = f"[REFLECT] Unknown outcome: {outcome}"

        self._append(note)
        return note

    def reset(self):
        """Restart the agent for a new game over the same range."""
        self.__init__(self._orig_low, self._orig_high)

    @property
    def range_size(self) -> int:
        return max(0, self.high - self.low + 1)

    @property
    def progress_pct(self) -> float:
        """0–100 % narrowed from original range."""
        orig = self._orig_high - self._orig_low + 1
        if orig <= 1:
            return 100.0
        return round((1 - self.range_size / orig) * 100, 1)

    # ── private ─────────────────────────────────────────────────────────────

    def _append(self, msg: str):
        self.log.append(msg)
