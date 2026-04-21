-- Run this once in the Supabase SQL editor to enable the Memorise page.
-- It creates a small table that tracks spaced-repetition state for each word.

create table if not exists vocab_reviews (
    word            text primary key references missing_words(word) on delete cascade,
    interval_days   integer not null default 0,
    next_due        date    not null default current_date,
    correct_count   integer not null default 0,
    wrong_count     integer not null default 0,
    last_reviewed   timestamptz
);

create index if not exists vocab_reviews_next_due_idx on vocab_reviews(next_due);

-- Match the RLS posture of the existing tables in this project
-- (missing_words, translation_scores) so the anon key used by the Streamlit
-- app can read and write. If your project DOES use RLS, replace this with
-- explicit policies instead.
alter table vocab_reviews disable row level security;
