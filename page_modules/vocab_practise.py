"""
Practise Vocabulary — where new and difficult words get learned.

Memorise handles scheduled review; this page gets words ready for it.

How a session works:
  - About 12 cards: words you're still learning, recently added words,
    words Memorise shows you struggle with, plus a few known words mixed in.
  - Each card hides the answer. Recall it, press "Show answer", then rate
    yourself Again / Hard / Good / Easy (keys: Space, 1-4).
  - "Again" brings the card back a few cards later. The session ends when
    every card has been rated Hard or better.
  - A word graduates to Memorise after 2 sessions in a row where you got it
    on the first try (or straight away if you rate a brand-new word "Easy").

Card types change as a word becomes familiar:
  new -> French to English; learning -> English to French;
  nearly known -> listening or fill-in-the-blank.
"""
import html
import random
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import streamlit as st
import streamlit.components.v1 as components

from core.audio import tts_bytes
from core.database_supabase import SupabaseDB
from core.llm_utils import LLMUtils

llm_utils = LLMUtils()
db = SupabaseDB()

SESSION_SIZE = 12
MAX_LEARNING = 6
MAX_NEW = 5
MAX_STRUGGLING = 3
MAX_KNOWN = 3
REQUEUE_GAP = 3          # an "Again" card comes back after this many cards
STRUGGLE_COOLDOWN = 3    # days before a struggling word is pulled in again

RATINGS = [
    ("again", "Again · 1"),
    ("hard", "Hard · 2"),
    ("good", "Good · 3"),
    ("easy", "Easy · 4"),
]
SHOW_ANSWER_LABEL = "Show answer · Space"
SESSION_KEYS = ("pr_queue", "pr_total", "pr_done", "pr_first", "pr_revealed", "pr_removed", "pr_error")

KIND_LABELS = {
    "recognise": "🇫🇷 → 🇬🇧  What does it mean?",
    "recall": "🇬🇧 → 🇫🇷  Say it in French",
    "listen": "🎧  Listen — what does it mean?",
    "cloze": "✏️  Fill in the blank",
}


# --------------------------- Styles ---------------------------

def _styles():
    st.markdown("""
    <style>
        .pr-card {
            background: white;
            border-radius: 20px;
            padding: 1.8rem 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            max-width: 640px;
            margin: 0.5rem auto 1rem auto;
            text-align: center;
        }
        .pr-card * { color: #1a1a2e; }
        .pr-kind { font-size: 0.9rem; color: #888 !important; margin-bottom: 0.8rem; display: block; }
        .pr-prompt { font-size: 2.1rem; font-weight: 700; display: block; line-height: 1.3; }
        .pr-hint { font-size: 1rem; color: #777 !important; margin-top: 0.6rem; display: block; }
        .pr-answer { border-top: 1px solid #e5e5e5; margin-top: 1.2rem; padding-top: 1.2rem; text-align: left; }
        .pr-word { font-size: 1.6rem; font-weight: 700; }
        .pr-badge {
            display: inline-block; font-size: 0.75rem; font-weight: 600;
            padding: 2px 8px; border-radius: 10px; margin-left: 8px; vertical-align: middle;
        }
        .pr-badge.m { background: #dbeafe; color: #1e40af !important; }
        .pr-badge.f { background: #fce7f3; color: #9d174d !important; }
        .pr-meaning { font-size: 1.1rem; color: #444 !important; margin: 0.3rem 0 1rem 0; }
        .pr-ex { margin: 0.55rem 0; }
        .pr-ex-fr { font-size: 1.05rem; display: block; }
        .pr-ex-en { font-size: 0.9rem; color: #888 !important; display: block; }
        .pr-ex mark { background: #fef08a; padding: 0 2px; border-radius: 3px; }
        .pr-related { margin-top: 1rem; font-size: 0.95rem; color: #555 !important; }
        /* The app's global button styles leave the popover button white on white. */
        [data-testid="stPopover"] button {
            background: rgba(255,255,255,0.08) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.25) !important;
        }
        [data-testid="stPopover"] button * { color: white !important; }
        [data-testid="stPopoverBody"] {
            background: #1f2028 !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
        }
        [data-testid="stPopoverBody"] * { color: white !important; }
        [data-testid="stPopoverBody"] > div { background: transparent !important; }
        [data-testid="stPopoverBody"] [data-baseweb="input"],
        [data-testid="stPopoverBody"] [data-baseweb="base-input"],
        [data-testid="stPopoverBody"] input { background: #2c2d38 !important; }
    </style>
    """, unsafe_allow_html=True)


def _keyboard_shortcuts():
    """Space reveals the answer, 1-4 rate the card. Ignored while typing."""
    components.html("""
    <script>
    const win = window.parent;
    if (!win.__practiseKeys) {
      win.__practiseKeys = true;
      const doc = win.document;
      const map = {' ': 'Show answer', '1': 'Again', '2': 'Hard', '3': 'Good', '4': 'Easy'};
      doc.addEventListener('keydown', (e) => {
        const label = map[e.key];
        if (!label || e.metaKey || e.ctrlKey || e.altKey) return;
        const t = e.target || {};
        const tag = (t.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select' || t.isContentEditable) return;
        if (e.key === ' ' && tag === 'button') return;
        const btn = Array.from(doc.querySelectorAll('button'))
          .find(b => b.innerText.trim().startsWith(label) && !b.disabled);
        if (btn) { e.preventDefault(); btn.click(); }
      });
    }
    </script>
    """, height=1)  # height=0 is treated as "default" (150px)


# --------------------------- Helpers ---------------------------

def _with_article(word: str, content) -> str:
    """'maison' + 'la' -> 'la maison'; leaves words that already have one."""
    article = (content or {}).get("article")
    if not article:
        return word
    lower = word.lower()
    if lower.startswith(("le ", "la ", "les ", "l'", "l’")):
        return word
    return f"l'{word}" if article == "l'" else f"{article} {word}"


def _highlight(sentence: str, word: str) -> str:
    """Escape a sentence and mark where the word appears."""
    safe = html.escape(sentence)
    target = html.escape(word.strip())
    if not target:
        return safe
    return re.sub(re.escape(target), lambda m: f"<mark>{m.group(0)}</mark>", safe, flags=re.IGNORECASE)


def _pick_kind(card) -> str:
    content = card.get("content") or {}
    # Words already in Memorise skip the easy first step.
    if card["origin"] == "new" or (card["stage"] != "graduated" and card["times_seen"] == 0):
        return "recognise"
    if card["stage"] == "learning" and card["good_streak"] == 0:
        return "recall"
    options = ["recall", "listen"]
    if content.get("cloze"):
        options.append("cloze")
    return random.choice(options)


def _clear_session():
    for k in SESSION_KEYS:
        st.session_state.pop(k, None)


# --------------------------- Building a session ---------------------------

def _choose_words(overview):
    """Pick this session's words: learning, new, struggling, then known."""
    learning = sorted(
        (w for w in overview if w["stage"] == "learning"),
        key=lambda w: w["last_practised"] or "",
    )
    new = sorted(
        (w for w in overview if w["stage"] == "new"),
        key=lambda w: w["added_on"] or "",
        reverse=True,
    )
    cutoff = (date.today() - timedelta(days=STRUGGLE_COOLDOWN)).isoformat()
    struggling = [
        w for w in overview
        if w["stage"] == "graduated"
        and w["wrong_count"] >= 2
        and w["wrong_count"] >= w["correct_count"]
        and (w["last_practised"] or "")[:10] < cutoff
    ]
    struggling_words = {w["word"] for w in struggling}
    known = [w for w in overview if w["stage"] == "graduated" and w["word"] not in struggling_words]

    for w in learning:
        w["origin"] = "learning"
    for w in new:
        w["origin"] = "new"
    for w in struggling:
        w["origin"] = "struggling"
    for w in known:
        w["origin"] = "known"

    picked = learning[:MAX_LEARNING]
    # Take more new words when there's little in progress.
    new_take = max(MAX_NEW, MAX_LEARNING + MAX_NEW - len(picked) - 2)
    picked += new[:new_take]
    picked += random.sample(struggling, min(len(struggling), MAX_STRUGGLING))

    known_take = min(len(known), MAX_KNOWN)
    picked = picked[:SESSION_SIZE - known_take]
    # Nothing new to learn? Fill the session with known words instead.
    known_take = min(len(known), max(known_take, SESSION_SIZE - len(picked)))
    picked += random.sample(known, known_take)
    return picked


def _fill_missing_content(cards):
    """Generate card content for words that don't have it yet, in parallel."""
    missing = [c for c in cards if not c.get("content")]
    if not missing:
        return
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda c: llm_utils.generate_card_content(c["word"], c["meaning"]), missing))
    for card, content in zip(missing, results):
        if not content:
            continue
        card["content"] = content
        try:
            db.save_card_content(card["word"], content, card["stage"])
        except Exception as e:
            print(f"Could not save card content for {card['word']!r}: {e}")


def _start_session(overview):
    cards = _choose_words(overview)
    with st.spinner("Preparing your cards..."):
        _fill_missing_content(cards)
    for card in cards:
        card["kind"] = _pick_kind(card)
    random.shuffle(cards)
    st.session_state.pr_queue = cards
    st.session_state.pr_total = len(cards)
    st.session_state.pr_done = []
    st.session_state.pr_first = {}
    st.session_state.pr_revealed = False
    st.session_state.pr_removed = 0
    st.session_state.pr_error = None


# --------------------------- Actions ---------------------------

def _rate(card, rating):
    first = st.session_state.pr_first.setdefault(card["word"], rating)
    queue = st.session_state.pr_queue
    queue.pop(0)
    st.session_state.pr_revealed = False

    if rating == "again":
        queue.insert(min(REQUEUE_GAP, len(queue)), card)
        return

    try:
        new_stage, _ = db.record_practice_result(
            card["word"], first, card["stage"], card["good_streak"], card["times_seen"]
        )
    except Exception as e:
        st.session_state.pr_error = f"Could not save progress for '{card['word']}': {e}"
        new_stage = card["stage"]
    st.session_state.pr_done.append({
        "word": card["word"],
        "first": first,
        "graduated": new_stage == "graduated" and card["stage"] != "graduated",
    })


def _remove_from_queue(word):
    st.session_state.pr_queue = [c for c in st.session_state.pr_queue if c["word"] != word]
    st.session_state.pr_revealed = False


def _skip_too_easy(card):
    try:
        db.skip_to_review(card["word"])
    except Exception as e:
        st.session_state.pr_error = f"Could not move '{card['word']}' to Memorise: {e}"
        return
    _remove_from_queue(card["word"])
    st.session_state.pr_done.append({"word": card["word"], "first": "easy", "graduated": True})


def _delete(card):
    try:
        db.delete_saved_word(card["word"])
    except Exception as e:
        st.session_state.pr_error = f"Could not delete '{card['word']}': {e}"
        return
    _remove_from_queue(card["word"])
    st.session_state.pr_removed += 1


def _save_meaning(card, new_meaning):
    new_meaning = new_meaning.strip()
    if not new_meaning or new_meaning == card["meaning"]:
        return
    try:
        db.update_meaning(card["word"], new_meaning)
    except Exception as e:
        st.session_state.pr_error = f"Could not update the meaning: {e}"
        return
    for c in st.session_state.pr_queue:
        if c["word"] == card["word"]:
            c["meaning"] = new_meaning


# --------------------------- Rendering ---------------------------

def _render_stage_counts(overview):
    counts = {"new": 0, "learning": 0, "graduated": 0}
    for w in overview:
        counts[w["stage"]] = counts.get(w["stage"], 0) + 1
    c1, c2, c3 = st.columns(3)
    c1.metric("🌱 New", counts["new"])
    c2.metric("📖 Learning", counts["learning"])
    c3.metric("🎓 In Memorise", counts["graduated"])


def _render_front(card):
    content = card.get("content") or {}
    kind = card["kind"]
    label = KIND_LABELS[kind]

    if kind == "recognise":
        prompt = html.escape(_with_article(card["word"], content))
        hint = ""
    elif kind == "recall":
        prompt = html.escape(card["meaning"])
        hint = ""
    elif kind == "listen":
        prompt = "🔊"
        hint = "Play the audio below"
    else:  # cloze
        cloze = content["cloze"]
        prompt = html.escape(cloze["sentence"]).replace("___", "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>")
        hint = f"Hint: {html.escape(card['meaning'])}"

    # Built without indentation or blank lines: Markdown would turn
    # indented HTML into a code block.
    hint_html = f"<span class='pr-hint'>{hint}</span>" if hint else ""
    size = "font-size:1.5rem;" if kind == "cloze" else ""
    return (
        f"<span class='pr-kind'>{label}</span>"
        f"<span class='pr-prompt' style='{size}'>{prompt}</span>"
        f"{hint_html}"
    )


def _render_back(card):
    content = card.get("content") or {}
    word_label = html.escape(_with_article(card["word"], content))
    gender = content.get("gender")
    badge = ""
    if gender == "m":
        badge = "<span class='pr-badge m'>masculine</span>"
    elif gender == "f":
        badge = "<span class='pr-badge f'>feminine</span>"

    parts = [
        "<div class='pr-answer'>",
        f"<div><span class='pr-word'>{word_label}</span>{badge}</div>",
        f"<div class='pr-meaning'>{html.escape(card['meaning'])}</div>",
    ]
    if card["kind"] == "cloze" and content.get("cloze"):
        parts.append(
            f"<div class='pr-ex'><span class='pr-ex-fr'>✏️ Answer: <mark>{html.escape(content['cloze']['answer'])}</mark></span></div>"
        )
    for ex in content.get("examples") or []:
        parts.append(
            "<div class='pr-ex'>"
            f"<span class='pr-ex-fr'>{_highlight(ex['fr'], card['word'])}</span>"
            f"<span class='pr-ex-en'>{html.escape(ex.get('en', ''))}</span>"
            "</div>"
        )
    if content.get("related"):
        parts.append(f"<div class='pr-related'>🔗 {html.escape(content['related'])}</div>")
    if not content:
        parts.append("<div class='pr-related'>Examples couldn't be generated for this word.</div>")
    parts.append("</div>")
    return "".join(parts)


def _render_card(card):
    revealed = st.session_state.pr_revealed
    content = card.get("content") or {}
    spoken_word = _with_article(card["word"], content)

    body = _render_front(card)
    if revealed:
        body += _render_back(card)
    st.markdown(f"<div class='pr-card'>{body}</div>", unsafe_allow_html=True)

    # Audio: the listening card plays up front; every card plays on reveal.
    try:
        if card["kind"] == "listen" or revealed:
            st.audio(tts_bytes(spoken_word), format="audio/mp3", autoplay=True)
        if revealed and content.get("examples"):
            with st.expander("🔊 Hear the examples"):
                examples_text = " ... ".join(ex["fr"] for ex in content["examples"])
                st.audio(tts_bytes(examples_text), format="audio/mp3")
    except Exception as e:
        st.caption(f"Audio unavailable: {e}")

    if not revealed:
        if st.button(SHOW_ANSWER_LABEL, use_container_width=True, type="primary"):
            st.session_state.pr_revealed = True
            st.rerun()
    else:
        cols = st.columns(4)
        for col, (rating, label) in zip(cols, RATINGS):
            with col:
                if st.button(label, use_container_width=True, key=f"rate_{rating}"):
                    _rate(card, rating)
                    st.rerun()


def _render_more_menu(card):
    with st.popover("⋯ More", use_container_width=True):
        new_meaning = st.text_input("Meaning", value=card["meaning"], key=f"pr_meaning_{card['word']}")
        if st.button("💾 Save meaning", use_container_width=True, key="pr_save_meaning"):
            _save_meaning(card, new_meaning)
            st.rerun()
        st.divider()
        if st.button("⏭ Too easy — move to Memorise", use_container_width=True, key="pr_skip"):
            _skip_too_easy(card)
            st.rerun()
        if st.button("🗑 Delete word", use_container_width=True, key="pr_delete"):
            _delete(card)
            st.rerun()


def _render_summary():
    done = st.session_state.pr_done
    graduated = [d["word"] for d in done if d["graduated"]]
    shaky = [d["word"] for d in done if d["first"] in ("again", "hard") and not d["graduated"]]
    first_try = sum(1 for d in done if d["first"] in ("good", "easy"))

    st.success(f"Session complete — {len(done)} words practised, {first_try} recalled on the first try.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**🎓 Moved to Memorise ({len(graduated)})**")
        st.write(", ".join(graduated) if graduated else "—")
    with c2:
        st.markdown(f"**🔁 Still shaky ({len(shaky)})**")
        st.write(", ".join(shaky) if shaky else "—")
    if st.session_state.pr_removed:
        st.caption(f"{st.session_state.pr_removed} word(s) deleted during the session.")

    if st.button("▶ Start another session", use_container_width=True, type="primary"):
        _clear_session()
        st.rerun()


# --------------------------- Entry point ---------------------------

def vocab_practise():
    _styles()
    st.divider()
    st.markdown("### 📖 Practise Vocabulary")
    st.caption(
        "Learn new and difficult words here. Recall the answer, reveal it, then rate yourself. "
        "Words you get right in two sessions in a row move on to Memorise."
    )

    try:
        overview = db.get_practice_overview()
    except Exception as e:
        st.error(
            "The practice table isn't reachable. Run the migration once in the Supabase SQL editor: "
            "`data/vocab_practice_migration.sql` (Memorise's `data/vocab_reviews_migration.sql` is needed too)."
        )
        st.caption(f"Details: {e}")
        return

    if not overview:
        st.info("No words yet. Add some on the Explore Vocabulary page first.")
        return

    if st.session_state.get("pr_error"):
        st.error(st.session_state.pr_error)
        st.session_state.pr_error = None

    # Start screen.
    if "pr_queue" not in st.session_state:
        _render_stage_counts(overview)
        st.write("")
        if st.button("▶ Start practice", use_container_width=True, type="primary"):
            _start_session(overview)
            st.rerun()
        st.caption("About 12 cards per session. Keys: Space shows the answer, 1–4 rate it.")
        return

    queue = st.session_state.pr_queue
    if not queue:
        _render_summary()
        return

    _keyboard_shortcuts()
    total = max(st.session_state.pr_total - st.session_state.pr_removed, 1)
    done = len(st.session_state.pr_done)
    st.progress(min(done / total, 1.0), text=f"{done} of {total} words done")

    card = queue[0]
    _render_card(card)

    st.write("")
    left, right = st.columns([3, 1])
    with left:
        if st.button("✕ End session", key="pr_end"):
            _clear_session()
            st.rerun()
    with right:
        _render_more_menu(card)
