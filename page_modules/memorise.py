"""
Memorise page — AI-powered vocabulary practice.

Two modes:
  - Review : 10 spaced-repetition flashcards per session. Prompt direction is
             randomised per card (EN->FR or FR->EN). LLM grades the answer and
             the schedule for that word is advanced or reset.
  - Story  : Pick 5-10 words from your vocabulary and the LLM weaves them into
             a short French story with an English translation.
"""
import random
import streamlit as st

from core.database_supabase import SupabaseDB
from core.llm_utils import LLMUtils

llm_utils = LLMUtils()
supabase_client = SupabaseDB()

SESSION_SIZE = 10
STORY_MIN, STORY_MAX = 5, 10


def _vocab_reviews_ready():
    """
    Preflight check: make sure the vocab_reviews table exists and is readable.
    Returns True if OK, otherwise renders an error and returns False.
    """
    try:
        supabase_client.supabase.table('vocab_reviews').select('word').limit(1).execute()
        return True
    except Exception as e:
        st.error(
            "The `vocab_reviews` table isn't reachable. "
            "If this is your first time using the Memorise page, run the migration once in the Supabase SQL editor: "
            "`data/vocab_reviews_migration.sql`."
        )
        st.caption(f"Details: {e}")
        return False


# --------------------------- Review mode ---------------------------

def _start_review_session():
    """Load up to SESSION_SIZE due words and randomise direction for each card."""
    try:
        due = supabase_client.get_due_words(limit=SESSION_SIZE)
    except Exception as e:
        st.error(f"Could not load due words: {e}")
        due = []
    cards = []
    for item in due:
        direction = random.choice(["EN->FR", "FR->EN"])
        if direction == "EN->FR":
            prompt = item["meaning"]
            expected = item["word"]
        else:
            prompt = item["word"]
            expected = item["meaning"]
        cards.append({
            "word": item["word"],
            "meaning": item["meaning"],
            "direction": direction,
            "prompt": prompt,
            "expected": expected,
        })
    st.session_state.mem_cards = cards
    st.session_state.mem_index = 0
    st.session_state.mem_result = None
    st.session_state.mem_correct = 0
    st.session_state.mem_wrong = 0


def _render_review():
    st.markdown("#### 🧠 Review Session")
    st.caption(f"{SESSION_SIZE} spaced-repetition cards. Direction is random. The AI grades flexibly (typos and accents OK).")

    if not _vocab_reviews_ready():
        return

    # Session status line.
    try:
        due_total = supabase_client.count_due_today()
    except Exception as e:
        due_total = None
        st.warning(f"Could not count due words: {e}")
    if due_total is not None:
        st.info(f"Words due today: **{due_total}**")

    # Kick off a session or pick up where we left off.
    if "mem_cards" not in st.session_state:
        if st.button("▶ Start review session", use_container_width=True):
            _start_review_session()
            st.rerun()
        return

    cards = st.session_state.mem_cards
    if not cards:
        st.success("Nothing due right now — come back later or add more words first.")
        if st.button("Close session"):
            for k in ("mem_cards", "mem_index", "mem_result", "mem_correct", "mem_wrong"):
                st.session_state.pop(k, None)
            st.rerun()
        return

    idx = st.session_state.mem_index
    if idx >= len(cards):
        _render_session_summary()
        return

    card = cards[idx]

    # Progress header.
    st.progress((idx) / len(cards), text=f"Card {idx + 1} of {len(cards)}")

    # Prompt card.
    arrow = "🇬🇧 → 🇫🇷" if card["direction"] == "EN->FR" else "🇫🇷 → 🇬🇧"
    st.markdown(f"<p style='opacity:0.7; margin-bottom:4px;'>{arrow}</p>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="card" style="text-align:center;">
            <div style="font-size:2rem; font-weight:700;">{card['prompt']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Answer box (disabled after grading so the learner sees the verdict).
    already_graded = st.session_state.mem_result is not None
    user_answer = st.text_input(
        "Your answer",
        key=f"mem_answer_{idx}",
        placeholder="Type the translation..." ,
        disabled=already_graded,
    )

    col1, col2 = st.columns(2)
    with col1:
        if not already_graded and st.button("✅ Check", use_container_width=True):
            if not user_answer.strip():
                st.warning("Type something first.")
            else:
                with st.spinner("Grading..."):
                    result = llm_utils.judge_answer(
                        direction=card["direction"],
                        prompt_word=card["prompt"],
                        expected=card["expected"],
                        user_answer=user_answer.strip(),
                    )
                try:
                    supabase_client.update_review(card["word"], result["correct"])
                except Exception as e:
                    st.error(f"Could not save review for '{card['word']}': {e}")
                    return
                if result["correct"]:
                    st.session_state.mem_correct += 1
                else:
                    st.session_state.mem_wrong += 1
                st.session_state.mem_result = result
                st.rerun()

    with col2:
        if already_graded and st.button("Next ▶", use_container_width=True):
            st.session_state.mem_index += 1
            st.session_state.mem_result = None
            st.rerun()

    # Show verdict below.
    if already_graded:
        result = st.session_state.mem_result
        if result["correct"]:
            st.success(f"Correct! Expected: **{card['expected']}**")
        else:
            st.error(f"Not quite. Expected: **{card['expected']}**")
        if result.get("note"):
            st.caption(result["note"])


def _render_session_summary():
    correct = st.session_state.get("mem_correct", 0)
    wrong = st.session_state.get("mem_wrong", 0)
    total = correct + wrong
    st.success(f"Session complete — {correct}/{total} correct.")
    if st.button("🔄 Start another session", use_container_width=True):
        _start_review_session()
        st.rerun()
    if st.button("Close", use_container_width=True):
        for k in ("mem_cards", "mem_index", "mem_result", "mem_correct", "mem_wrong"):
            st.session_state.pop(k, None)
        st.rerun()


# --------------------------- Story mode ---------------------------

def _render_story():
    st.markdown("#### 📖 Story Mode")
    st.caption(f"Pick {STORY_MIN}-{STORY_MAX} words from your last {STORY_MAX} reviewed words. The AI will weave them into a short French story with an English translation.")

    if not _vocab_reviews_ready():
        return

    try:
        words_data = supabase_client.get_recently_reviewed(limit=STORY_MAX)
    except Exception as e:
        st.error(f"Could not load recent reviews: {e}")
        return

    if not words_data:
        st.info("No recently reviewed words yet. Run a Review session first, then come back to create a story.")
        return

    if len(words_data) < STORY_MIN:
        st.warning(
            f"Only {len(words_data)} recently reviewed word(s) available — you need at least {STORY_MIN}. "
            "Review a few more cards first."
        )
        return

    word_labels = {f"{w['word']} — {w['meaning']}": w['word'] for w in words_data}
    selection = st.multiselect(
        f"Pick {STORY_MIN}-{STORY_MAX} words from your last {len(words_data)} reviewed",
        options=list(word_labels.keys()),
        max_selections=STORY_MAX,
    )
    picked = [word_labels[label] for label in selection]

    if st.button("✨ Generate story", use_container_width=True, disabled=len(picked) < STORY_MIN):
        with st.spinner("Writing your story..."):
            story = llm_utils.generate_story(picked)
        st.session_state.mem_last_story = story

    if len(picked) < STORY_MIN:
        st.caption(f"Select at least {STORY_MIN} words to enable the generator.")

    story = st.session_state.get("mem_last_story")
    if story:
        st.markdown("---")
        st.markdown(story)


# --------------------------- Entry point ---------------------------

def memorise():
    st.divider()
    st.markdown("### 🧠 Memorise")
    st.caption("AI-powered spaced-repetition review plus story mode to lock words into memory.")

    mode = st.radio(
        "Mode",
        ["Review", "Story"],
        horizontal=True,
        label_visibility="collapsed",
    )

    st.write("")

    if mode == "Review":
        _render_review()
    else:
        _render_story()
