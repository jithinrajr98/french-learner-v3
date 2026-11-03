-- Run this once in the Supabase SQL editor to enable the redesigned
-- Practise Vocabulary page. It stores each word's learning stage and the
-- AI-generated card content (examples, gender, fill-in-the-blank) so cards
-- load instantly and show the same examples every time.

create table if not exists vocab_practice (
    word            text primary key references missing_words(word) on delete cascade,
    stage           text    not null default 'new'
                    check (stage in ('new', 'learning', 'graduated')),
    good_streak     integer not null default 0,
    times_seen      integer not null default 0,
    last_practised  timestamptz,
    article         text,
    gender          text,
    examples        jsonb,
    cloze           jsonb,
    related         text
);

create index if not exists vocab_practice_stage_idx on vocab_practice(stage);

-- Same RLS posture as vocab_reviews so the app's anon key can read and write.
alter table vocab_practice disable row level security;
