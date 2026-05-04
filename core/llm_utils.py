import re, os
from config.settings import GROQ_MODEL
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
import streamlit as st


class LLMUtils:

    def __init__(self):
        """
        Initialize the LLMUtils class with a Groq client.
        """
        # Try Streamlit secrets first (for cloud deployment), then env vars (for local dev)
        try:
            api_key = st.secrets["GROQ_API_KEY"]
        except (KeyError, FileNotFoundError):
            api_key = os.getenv('GROQ_API_KEY')

        if not api_key:
            raise ValueError("GROQ_API_KEY not found in Streamlit secrets or environment variables.")

        self.api_key = api_key
        self.groq_client = Groq(api_key=self.api_key)  
        
    
    def get_french_word_meaning(self, word: str) -> str:
        """
        Get the meaning of a French word using a language model.
        """
        prompt = f"""Please provide the meaning of the French word '{word}' in English. Return up to 3 meanings as a single comma seperated list. 
        Do not explain or add any additional text.
        Fromat the output as : 'meaning1, meaning2, meaning3'."""
        response = self.groq_client.chat.completions.create(
            messages=[
             {"role": "user", "content": prompt}],
            model=GROQ_MODEL )
        
        return response.choices[0].message.content.strip()
    
    
    def correct_french_accents(self, word: str) -> str:
        prompt = f"""Correct any accent errors in this French text: "{word}"
        
        Important rules:
            1. Return ONLY the corrected French text with proper accents (é, è, ê, ë, à, â, ä, ç, î, ï, ô, ö, ù, û, ü, ÿ)
            2. Do not change correct accents that are already present
            3. If the input has no accent errors, return it exactly as-is
            4. Never add any explanation, commentary, or additional text
            5. Preserve all capitalization, spaces, and punctuation exactly as in the input
            6. Do not modify the text in any way other than correcting accents
            7. Do not add any additional quotes or formatting
            
            Return ONLY the corrected text:"""
        
        response = self.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_MODEL )
        
        response = response.choices[0].message.content.strip()
        response = re.sub(r'^[\'"]|[\'"]$', '', response)
        response = re.sub(r'^[\'"]|[\'"]$', '', response)
        return response
    
    
    def example_sentence_generator(self, word: str) -> str:
            """
            Generate an simple example french sentence using the given French word.
            
            Args:
                word: The French word to use in the example sentence
            
            Returns:
                A sentence that includes the French word
            """
            prompt = f"Generate a french sentence using the French word '{word}'. Only return the sentence without any explanation or additional text."
            
            response = self.groq_client.chat.completions.create(
                    messages=[
                    {"role": "user", "content": prompt}],
                    model=GROQ_MODEL )
            
            return response.choices[0].message.content.strip()


    # ========= Memorise page helpers =========

    def judge_answer(self, direction: str, prompt_word: str, expected: str, user_answer: str):
        """
        Grade a flashcard answer. `direction` is "EN->FR" or "FR->EN".
        Returns a dict: {"correct": bool, "note": str}.
        Accepts typos, missing accents, and valid synonyms as correct.
        """
        prompt = f"""You are grading a French vocabulary flashcard.

Direction: {direction}
Prompt shown to learner: {prompt_word}
Expected answer (reference): {expected}
Learner's answer: {user_answer}

Rules:
- Typos, missing accents, and close synonyms count as CORRECT.
- If the meaning column has multiple options (comma separated), any one of them is CORRECT.
- Conjugated or differently inflected forms of the right root count as CORRECT.
- A blank or completely unrelated answer is WRONG.

Respond in EXACTLY this format, two lines, no extra text:
Line 1: CORRECT or WRONG
Line 2: one short sentence (max 15 words) explaining why, or giving the better answer."""

        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL,
                temperature=0.0,
            )
            text = response.choices[0].message.content.strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            verdict = (lines[0] if lines else "").upper()
            note = lines[1] if len(lines) > 1 else ""
            return {"correct": verdict.startswith("CORRECT"), "note": note}
        except Exception as e:
            return {"correct": False, "note": f"Grader error: {e}"}

    def generate_story(self, words):
        """
        Generate a short French story that uses the given words, followed by
        an English translation. Returns a single string with two sections.
        """
        word_list = ", ".join(words)
        prompt = f"""Write a short, simple French story (5-8 sentences) that naturally uses ALL of these French words: {word_list}.

Requirements:
- Use each listed word at least once. Wrap each use in **double asterisks** so it is easy to spot.
- Keep vocabulary around A2-B1 level outside of the target words.
- Make it a coherent little scene, not a list of sentences.
- After the French story, add a blank line, then the line "English translation:" and a faithful English translation (also bolding the equivalent English words).

Output only the story and its translation, no preamble, no extra commentary."""

        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating story: {e}"

    def generate_writing_exercise(self, words):
        """
        Generate a single English sentence that uses the given French words
        (by their English meanings), plus a reference French translation of
        the sentence. Returns {"english": str, "reference_french": str}.
        """
        word_list = ", ".join(words)
        prompt = f"""You are creating a French translation practice exercise.

Target French words to feature: {word_list}

Task:
1. Write ONE short English sentence that NATURALLY uses the English meaning of each target French word at least once.
2. Then provide the correct French translation of that sentence. The translation MUST use each of the target French words above (not synonyms).
3. Keep the language simple (A2-B1 level). No idioms, no fancy tenses.
4. Output exactly one sentence for English and one sentence for French.

Respond in EXACTLY this format, no extra text, no preamble:

ENGLISH:
<your single english sentence here>

FRENCH:
<reference french translation here>"""

        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL,
                temperature=0.5,
            )
            raw = response.choices[0].message.content.strip()
        except Exception as e:
            return {"english": "", "reference_french": "", "error": str(e)}

        # Parse the two sections.
        # The LLM mostly follows "ENGLISH:\n... \nFRENCH:\n..." but sometimes
        # it typos the second label (e.g. "FRENISH:") or puts everything on
        # one line. We use a fuzzy regex: match ENGLISH: and any token that
        # starts with FR followed by a colon — that catches FRENCH, FRENISH,
        # FRANCAIS, FR, etc. Case-insensitive.
        en_re = re.compile(r"(?i)english\s*:\s*")
        fr_re = re.compile(r"(?i)\bfr[a-z]*\s*:\s*")

        en_match = en_re.search(raw)
        # Skip any FR-label that happens to sit inside the ENGLISH label itself.
        fr_match = None
        search_from = en_match.end() if en_match else 0
        for m in fr_re.finditer(raw, pos=search_from):
            fr_match = m
            break

        if en_match and fr_match and en_match.start() < fr_match.start():
            english = raw[en_match.end():fr_match.start()]
            french = raw[fr_match.end():]
        elif fr_match and not en_match:
            english = raw[:fr_match.start()]
            french = raw[fr_match.end():]
        elif en_match and not fr_match:
            english = raw[en_match.end():]
            french = ""
        else:
            english = raw
            french = ""

        # Collapse whitespace/newlines inside each section.
        english = " ".join(english.split()).strip()
        french = " ".join(french.split()).strip()

        return {"english": english, "reference_french": french}
