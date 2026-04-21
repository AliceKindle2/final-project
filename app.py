import random
import streamlit as st
from logic_utils import (
    get_range_for_difficulty,
    get_attempt_limit,
    parse_guess,
    check_guess,
    update_score,
    AgentOpponent,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

# ── Sidebar ──────────────────────────────────────────────────────────────────

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit = get_attempt_limit(difficulty)          # FIX: single source of truth
low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

show_agent = st.sidebar.toggle("🤖 AI Opponent", value=True)

# ── Session state bootstrap ───────────────────────────────────────────────────

def _init_game():
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0           # FIX: start at 0; incremented on submit
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.agent = AgentOpponent(low, high)
    # Kick off the agent's first plan+act immediately
    guess, reasoning = st.session_state.agent.plan_and_act()
    st.session_state.agent_pending_guess = guess
    st.session_state.agent_pending_reason = reasoning

for key in ("secret", "attempts", "score", "status", "history", "agent"):
    if key not in st.session_state:
        _init_game()
        break

agent: AgentOpponent = st.session_state.agent

# ── New game button ───────────────────────────────────────────────────────────

if st.button("New Game 🔁"):
    _init_game()
    st.rerun()

# ── Status gate ──────────────────────────────────────────────────────────────

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won this round. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

# ── Main layout: player left, agent right ────────────────────────────────────

player_col, agent_col = st.columns([3, 2], gap="large")

# ── Player column ─────────────────────────────────────────────────────────────

with player_col:
    st.subheader("Your guess")

    attempts_left = attempt_limit - st.session_state.attempts   # FIX: no off-by-one
    # FIX: banner now uses actual difficulty range instead of hardcoded "1 to 100"
    st.info(f"Guess a number between **{low}** and **{high}**. Attempts left: **{attempts_left}**")

    raw_guess = st.text_input("Enter your guess:", key=f"guess_input_{difficulty}")

    col1, col2 = st.columns(2)
    with col1:
        submit = st.button("Submit Guess 🚀")
    with col2:
        show_hint = st.checkbox("Show hint", value=True)

    if submit and st.session_state.status == "playing":
        st.session_state.attempts += 1

        ok, guess_int, err = parse_guess(raw_guess)

        if not ok:
            st.session_state.history.append(raw_guess)
            st.error(err)
            st.session_state.attempts -= 1  # don't count malformed input
        else:
            st.session_state.history.append(guess_int)
            secret = st.session_state.secret
            outcome, message = check_guess(guess_int, secret)

            if show_hint:
                if outcome == "Win":
                    st.success(message)
                elif outcome == "Too High":
                    st.warning(message)
                else:
                    st.warning(message)

            st.session_state.score = update_score(
                current_score=st.session_state.score,
                outcome=outcome,
                attempt_number=st.session_state.attempts,
            )

            # ── Agent also learns from the human's result (same secret) ──
            if show_agent and not agent.solved:
                agent_outcome, _ = check_guess(
                    st.session_state.agent_pending_guess,
                    secret,
                )
                agent.reflect(agent_outcome)
                if not agent.solved:
                    g, r = agent.plan_and_act()
                    st.session_state.agent_pending_guess = g
                    st.session_state.agent_pending_reason = r

            if outcome == "Win":
                st.balloons()
                st.session_state.status = "won"
                st.success(
                    f"You won! The secret was **{secret}**. "
                    f"Final score: **{st.session_state.score}**"
                )
            elif st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! The secret was **{secret}**. "
                    f"Score: {st.session_state.score}"
                )

    if st.session_state.history:
        st.caption("Guess history: " + " → ".join(str(h) for h in st.session_state.history))

    st.metric("Score", st.session_state.score)

# ── Agent column ──────────────────────────────────────────────────────────────

if show_agent:
    with agent_col:
        st.subheader("🤖 AI Opponent")

        if agent.solved:
            st.success(f"Agent solved it in **{agent.guess_count}** guess(es)!")
        else:
            st.metric("Agent's current guess", st.session_state.get("agent_pending_guess", "—"))
            st.caption(f"Reasoning: {st.session_state.get('agent_pending_reason', '')}")
            st.progress(
                int(agent.progress_pct),
                text=f"Search space narrowed: {agent.progress_pct}%"
            )
            st.caption(
                f"Range remaining: [{agent.low}, {agent.high}] "
                f"({agent.range_size} values)"
            )

        with st.expander("🧠 Agent reasoning chain"):
            for line in agent.log:
                tag = line.split("]")[0].strip("[") if "]" in line else ""
                if tag == "PLAN":
                    st.info(line)
                elif tag == "ACT":
                    st.success(line)
                elif tag == "REFLECT":
                    st.warning(line)
                else:
                    st.caption(line)

        st.caption(
            f"Guess {agent.guess_count}/{agent.max_guesses} max theoretical guesses"
        )

# ── Debug expander ────────────────────────────────────────────────────────────

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
