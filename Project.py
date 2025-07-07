import streamlit as st
import requests
import random
import time
import os
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="🧠 Quote Quiz Game", layout="centered")
st.title("🧠 Quote Quiz Game")
st.text("To play this game, enter an amount for the timer and press start timer to begin. The quiz will be based on the keyword you searched for" \
"You can play until the timer ends or for however long you want. After pressing submit once, press submit again, so the next quote" \
"button will appear.")

api_key = os.getenv("API_KEY")

# Initialize session state defaults
defaults = {
    "score": 0, "attempts": 0, "quote": None, "correct": None, "options": [],
    "quotes": [], "keyword": "", "answered": False, "timer_end_time": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Timer UI and logic
minutes = st.number_input("⏱️ Timer (minutes)", min_value=0.0, step=0.5, value=1.0)
if st.button("▶️ Start Timer", disabled=st.session_state.timer_end_time is not None):
    if minutes > 0:
        st.session_state.timer_end_time = time.time() + int(minutes * 60)
    else:
        st.warning("Enter a positive time.")

if st.session_state.timer_end_time:
    st_autorefresh(interval=1000, key="timer_refresh")
    remaining = int(st.session_state.timer_end_time - time.time())
    if remaining > 0:
        m, s = divmod(remaining, 60)
        st.markdown(f"⏳ **Time Left:** {m:02d}:{s:02d}")
    else:
        st.session_state.timer_end_time = None
        st.success("⏰ Time's Up!")

st.markdown("---")

# Reset everything
if st.button("🔄 Reset Score & Timer"):
    for k, v in defaults.items():
        st.session_state[k] = v
    st.success("Reset done.")

st.markdown("---")

# Search quotes
keyword = st.text_input("🔍 Search keyword", value=st.session_state.keyword)
if st.button("Search", disabled=not keyword.strip()):
    st.session_state.keyword = keyword.strip()
    st.session_state.answered = False
    url = f"https://favqs.com/api/quotes/?filter={st.session_state.keyword}&type=keyword"
    headers = {"Authorization": f'Token token="{api_key}"'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        quotes = [q for q in res.json().get("quotes", []) if q.get("author") and q.get("body")]
        if quotes:
            st.session_state.quotes = quotes
            st.session_state.quote = None
            st.success(f"Found {len(quotes)} quotes for '{st.session_state.keyword}'.")
        else:
            st.warning("No quotes found with authors.")
    except Exception as e:
        st.error(f"API error: {e}")

st.markdown("---")

# Quiz
if st.session_state.quotes:
    st.markdown("### 🎯 Quiz")

    # Determine if Next Quote button is disabled:
    # Disable only if question not answered yet
    # Enable if answered (right or wrong)
    next_disabled = not st.session_state.answered

    if st.session_state.quote is None or st.button("➡️ Next Quote", disabled=next_disabled):
        q = random.choice(st.session_state.quotes)
        st.session_state.quote = q["body"]
        st.session_state.correct = q["author"]
        others = list({x["author"] for x in st.session_state.quotes if x["author"] != q["author"]})
        choices = random.sample(others, min(3, len(others))) + [q["author"]]
        random.shuffle(choices)
        st.session_state.options = choices
        st.session_state.answered = False

    st.markdown(f"> *{st.session_state.quote}*")

    answer = st.radio(
        "Who said this?",
        st.session_state.options,
        key="answer_radio",
        disabled=st.session_state.answered,
    )

    if st.button("✅ Submit Answer", disabled=st.session_state.answered):
        if not answer:
            st.warning("Select an answer before submitting.")
        else:
            st.session_state.attempts += 1
            st.session_state.answered = True
            if answer == st.session_state.correct:
                st.session_state.score += 1
                st.success("Correct! 🎉 You can now click Next Quote to continue.")
            else:
                st.error(f"Wrong. Correct answer: {st.session_state.correct}")

    st.markdown(f"**Score:** {st.session_state.score} / {st.session_state.attempts}")


else:
    st.info("Search for quotes to start the quiz!")
