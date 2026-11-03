from supabase import create_client, Client
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import streamlit as st
from core.llm_utils import LLMUtils
load_dotenv()

# Simple spaced-repetition interval ladder (days).
# On a correct answer we step forward one rung; on wrong we reset to the first rung.
SR_INTERVALS = [1, 3, 7, 14, 30, 90]

# Practise page: a word graduates to spaced review after this many sessions
# in a row where you recalled it on the first try ("Good" or "Easy").
PRACTICE_GRADUATE_STREAK = 2
PRACTICE_CONTENT_FIELDS = ('article', 'gender', 'examples', 'cloze', 'related')

class SupabaseDB:
    def __init__(self):
        # Try Streamlit secrets first (for cloud deployment), then env vars (for local dev)
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_API_KEY"]
        except (KeyError, FileNotFoundError):
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_API_KEY')
        self.supabase = create_client(url, key)
        self.llm_utils = LLMUtils()

    def get_all_saved_words(self):
        """Retrieve all saved words"""
        try:
            response = self.supabase.table('missing_words').select('*').order('added_on', desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching words: {e}")
            return []

    def delete_saved_word(self, word):
        """Delete a saved word"""
        try:
            self.supabase.table('missing_words').delete().eq('word', word).execute()
        except Exception as e:
            print(f"Error deleting word: {e}")

    # ========= Spaced-repetition helpers (used by the Memorise page) =========

    def get_due_words(self, limit: int = 10):
        """
        Return up to `limit` words that are due for review.
        A word is "due" if it has no review row yet (never studied) or if
        its next_due date is strictly before today. Never-studied words come first.
        Each item is a dict: {word, meaning, interval_days, next_due}.

        Raises on failure (e.g. vocab_reviews table missing).
        """
        all_words = self.supabase.table('missing_words').select('word, meaning').execute().data or []
        reviews = self.supabase.table('vocab_reviews').select('*').execute().data or []
        review_by_word = {r['word']: r for r in reviews}

        today = date.today().isoformat()
        never_studied = []
        due_studied = []
        for w in all_words:
            r = review_by_word.get(w['word'])
            if r is None:
                never_studied.append({
                    'word': w['word'],
                    'meaning': w['meaning'],
                    'interval_days': 0,
                    'next_due': today,
                })
            elif r.get('next_due') and str(r['next_due']) < today:
                # strictly less than today: only surface words whose scheduled
                # day has actually passed. Prevents re-showing a word you
                # reviewed moments ago when interval=1 (next_due == today).
                due_studied.append({
                    'word': w['word'],
                    'meaning': w['meaning'],
                    'interval_days': r.get('interval_days', 0),
                    'next_due': r['next_due'],
                })

        due_studied.sort(key=lambda x: x['next_due'])
        return (never_studied + due_studied)[:limit]

    def update_review(self, word: str, was_correct: bool):
        """
        Advance or reset the review schedule for a word.
        Uses an explicit update-if-exists-else-insert so we don't rely on
        PostgREST upsert semantics. Raises on failure.
        """
        existing = self.supabase.table('vocab_reviews').select('*').eq('word', word).execute().data
        row = existing[0] if existing else None

        if was_correct:
            current = row.get('interval_days', 0) if row else 0
            try:
                idx = SR_INTERVALS.index(current)
                next_idx = min(idx + 1, len(SR_INTERVALS) - 1)
            except ValueError:
                next_idx = 0
            new_interval = SR_INTERVALS[next_idx]
        else:
            new_interval = SR_INTERVALS[0]

        new_next_due = (date.today() + timedelta(days=new_interval)).isoformat()
        new_correct = (row.get('correct_count', 0) if row else 0) + (1 if was_correct else 0)
        new_wrong = (row.get('wrong_count', 0) if row else 0) + (0 if was_correct else 1)

        payload = {
            'interval_days': new_interval,
            'next_due': new_next_due,
            'correct_count': new_correct,
            'wrong_count': new_wrong,
            'last_reviewed': datetime.utcnow().isoformat(),
        }

        if row:
            response = (
                self.supabase.table('vocab_reviews')
                .update(payload)
                .eq('word', word)
                .execute()
            )
        else:
            payload['word'] = word
            response = self.supabase.table('vocab_reviews').insert(payload).execute()

        # Sanity check: if nothing was written, surface it as an error.
        if not getattr(response, 'data', None):
            raise RuntimeError(
                f"vocab_reviews write for '{word}' returned no rows — "
                "check that the vocab_reviews table exists and is writable."
            )

    def get_recently_reviewed(self, limit: int = 10):
        """
        Return the `limit` most recently reviewed words, newest first.
        Each item is a dict: {word, meaning, last_reviewed}.
        Words that have never been reviewed are excluded.
        Raises on failure (e.g. vocab_reviews table missing).
        """
        reviews = (
            self.supabase.table('vocab_reviews')
            .select('word, last_reviewed')
            .not_.is_('last_reviewed', 'null')
            .order('last_reviewed', desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )
        if not reviews:
            return []

        words = [r['word'] for r in reviews]
        meanings_data = (
            self.supabase.table('missing_words')
            .select('word, meaning')
            .in_('word', words)
            .execute()
            .data
            or []
        )
        meaning_by_word = {m['word']: m['meaning'] for m in meanings_data}

        result = []
        for r in reviews:
            if r['word'] in meaning_by_word:
                result.append({
                    'word': r['word'],
                    'meaning': meaning_by_word[r['word']],
                    'last_reviewed': r['last_reviewed'],
                })
        return result

    def count_due_today(self):
        """Count how many words are due today (including never-studied ones)."""
        try:
            all_words = self.supabase.table('missing_words').select('word').execute().data or []
            reviews = self.supabase.table('vocab_reviews').select('word, next_due').execute().data or []
            review_by_word = {r['word']: r for r in reviews}
            today = date.today().isoformat()
            return sum(
                1 for w in all_words
                if (w['word'] not in review_by_word) or (review_by_word[w['word']].get('next_due', today) <= today)
            )
        except Exception as e:
            print(f"Error in count_due_today: {e}")
            return 0

    # ========= Practice helpers (used by the Practise Vocabulary page) =========

    def get_practice_overview(self):
        """
        Load every saved word with its practice state and Memorise stats.

        Returns a list of dicts with: word, meaning, added_on, stage,
        good_streak, times_seen, last_practised, content, correct_count,
        wrong_count. `content` is the saved card content dict, or None.

        Stage is 'new', 'learning' or 'graduated'. A word with no practice
        row counts as graduated if Memorise already reviews it, else new.
        Raises on failure (e.g. vocab_practice table missing).
        """
        words = self.supabase.table('missing_words').select('word, meaning, added_on').execute().data or []
        practice_rows = self.supabase.table('vocab_practice').select('*').execute().data or []
        review_rows = (
            self.supabase.table('vocab_reviews')
            .select('word, correct_count, wrong_count')
            .execute()
            .data
            or []
        )
        practice = {r['word']: r for r in practice_rows}
        reviews = {r['word']: r for r in review_rows}

        overview = []
        for w in words:
            p = practice.get(w['word'])
            r = reviews.get(w['word'])
            if p:
                stage = p.get('stage') or 'new'
            elif r:
                stage = 'graduated'
            else:
                stage = 'new'
            content = None
            if p and p.get('examples'):
                content = {k: p.get(k) for k in PRACTICE_CONTENT_FIELDS}
            overview.append({
                'word': w['word'],
                'meaning': w.get('meaning') or '',
                'added_on': w.get('added_on') or '',
                'stage': stage,
                'good_streak': (p or {}).get('good_streak') or 0,
                'times_seen': (p or {}).get('times_seen') or 0,
                'last_practised': (p or {}).get('last_practised') or '',
                'content': content,
                'correct_count': (r or {}).get('correct_count') or 0,
                'wrong_count': (r or {}).get('wrong_count') or 0,
            })
        return overview

    def _save_practice(self, word: str, fields: dict, stage_if_new: str):
        """Update the word's practice row, or create it with `stage_if_new`."""
        existing = self.supabase.table('vocab_practice').select('word').eq('word', word).execute().data
        if existing:
            self.supabase.table('vocab_practice').update(fields).eq('word', word).execute()
        else:
            row = {'word': word, 'stage': stage_if_new, **fields}
            self.supabase.table('vocab_practice').insert(row).execute()

    def save_card_content(self, word: str, content: dict, stage: str):
        """Store AI-generated card content so it is reused next time."""
        fields = {k: content.get(k) for k in PRACTICE_CONTENT_FIELDS}
        self._save_practice(word, fields, stage)

    def _schedule_review(self, word: str, interval_days: int):
        """Hand a word to Memorise, unless Memorise already schedules it."""
        existing = self.supabase.table('vocab_reviews').select('word').eq('word', word).execute().data
        if existing:
            return
        self.supabase.table('vocab_reviews').insert({
            'word': word,
            'interval_days': interval_days,
            'next_due': (date.today() + timedelta(days=interval_days)).isoformat(),
            'correct_count': 0,
            'wrong_count': 0,
        }).execute()

    def record_practice_result(self, word: str, first_rating: str, stage: str,
                               good_streak: int, times_seen: int):
        """
        Save the outcome of one practice session for a word.
        `first_rating` is the first rating given in this session:
        'again', 'hard', 'good' or 'easy'.
        Returns (new_stage, new_good_streak).
        """
        if first_rating in ('good', 'easy'):
            streak = good_streak + 1
        elif first_rating == 'hard':
            streak = good_streak
        else:
            streak = 0

        known_on_sight = first_rating == 'easy' and times_seen == 0
        graduates_now = stage != 'graduated' and (streak >= PRACTICE_GRADUATE_STREAK or known_on_sight)
        new_stage = 'graduated' if (stage == 'graduated' or graduates_now) else 'learning'

        self._save_practice(word, {
            'stage': new_stage,
            'good_streak': streak,
            'times_seen': times_seen + 1,
            'last_practised': datetime.utcnow().isoformat(),
        }, new_stage)

        if graduates_now:
            self._schedule_review(word, SR_INTERVALS[0])
        return new_stage, streak

    def skip_to_review(self, word: str):
        """'Too easy': graduate the word now and schedule it a week out."""
        self._save_practice(word, {
            'stage': 'graduated',
            'last_practised': datetime.utcnow().isoformat(),
        }, 'graduated')
        self._schedule_review(word, 7)

    def update_meaning(self, word: str, meaning: str):
        """Correct a word's saved meaning."""
        self.supabase.table('missing_words').update({'meaning': meaning}).eq('word', word).execute()
