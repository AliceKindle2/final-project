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
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.agent = AgentOpponent(low, high)
    # Agent plans its first guess but it stays hidden until player submits
    guess, reasoning = st.session_state.agent.plan_and_act()
    st.session_state.agent_pending_guess = guess
    st.session_state.agent_pending_reason = reasoning
    st.session_state.agent_last_guess = None      # revealed after player submits
    st.session_state.agent_last_outcome = None
    st.session_state.agent_guess_revealed = False  # gate: show only after player acts
    st.session_state.agent_won = False             # tracks if agent solved before player

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
    player_won = st.session_state.status == "won"
    agent_won  = st.session_state.get("agent_won", False)

    if show_agent:
        st.divider()
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            if player_won:
                st.success("You won this round!")
            else:
                st.error("You ran out of attempts.")
        with res_col2:
            if agent_won and player_won:
                st.warning("🤝 It's a tie — you both found it!")
            elif agent_won:
                st.error(f"🤖 Agent wins! Solved in {st.session_state.agent.guess_count} guess(es).")
            elif player_won and not agent_won:
                st.success("🏆 You beat the AI!")
            else:
                st.info("🤖 Agent didn't solve it either — nobody wins!")
        st.divider()
    else:
        if player_won:
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

            # ── Reveal agent's pending guess now that player has submitted ──
            if show_agent and not agent.solved:
                agent_outcome, _ = check_guess(
                    st.session_state.agent_pending_guess,
                    secret,
                )
                # Save what the agent guessed THIS round so we can show it
                st.session_state.agent_last_guess = st.session_state.agent_pending_guess
                st.session_state.agent_last_outcome = agent_outcome
                st.session_state.agent_guess_revealed = True
                # Agent reflects and quietly plans its NEXT guess (stays hidden)
                agent.reflect(agent_outcome)
                if agent.solved:
                    st.session_state.agent_won = True
                else:
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
            # Show "calculating" until the player submits their first guess
            if not st.session_state.get("agent_guess_revealed"):
                st.caption("🤔 Calculating best guess...")
            else:
                st.caption("🤔 Calculating next guess...")

        # Show the agent's previous guesses (revealed ones only)
        act_lines = [l for l in agent.log if l.startswith("[ACT]")]
        # Hide the most recent ACT if the agent hasn't been revealed yet this round
        if not agent.solved:
            act_lines = act_lines[:-1]  # last one is the pending (hidden) guess

        if act_lines:
            st.caption("Previous guesses:")
            guesses_display = " → ".join(
                l.split(":")[1].strip() if ":" in l else "?"
                for l in act_lines
            )
            st.caption(guesses_display)

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

# ── Debug expander ────────────────────────────────────────────────────────────

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")