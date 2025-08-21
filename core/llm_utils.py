from typing import List, Dict, Any
from ast import literal_eval
import re, os
from config.settings import GROQ_MODEL, GROQ_TRANSCRIPT_MODEL
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
import streamlit as st


class LLMUtils:
    
    def __init__(self):
        """
        Initialize the LLMUtils class with a Groq client.
        """
        
         # Try to get API key from Streamlit secrets first, then environment variables
        api_key = None
        # Check Streamlit secrets
        if hasattr(st, 'secrets') and 'GROQ_API_KEY' in st.secrets:
            api_key = st.secrets['GROQ_API_KEY']
        # Fallback to environment variable
        elif 'GROQ_API_KEY' in os.environ:
            api_key = os.environ['GROQ_API_KEY']
        
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
        
        response.choices[0].message.content.strip()
        response = re.sub(r'^[\'"]|[\'"]$', '', response)
        response = re.sub(r'^[\'"]|[\'"]$', '', response)
        return response
    
    
    def extract_missed_words(self, correct: str, attempt: str) -> List[str]:
        """/nothink Identify missing words from user's translation attempt"""
        prompt = f"""
        Compare these French translations:
        Correct: {correct}
        Attempt: {attempt}
        
        Identify which  words (nouns, verbs, adjectives, adverbs) 
        from the correct translation are missing in the attempt.
        Return ONLY a Python list of the missing words in their base form.
        Example: ['mot1', 'mot2']
        """
        try:
            response = self.groq_client.chat.completions.create(
                messages=[
                {"role": "user", "content": prompt}],
                model=GROQ_MODEL )
            response = response.choices[0].message.content.strip()
        
            return literal_eval(response)
        except:
            return []





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
        
    
    def conjugation_details(self, word: str) -> str:
        """
        Get conjugation details for a French verb.
        
        Args:
            word: The French verb to conjugate
            
        Returns:
            A string with conjugation details or 'not a verb'
        """
        prompt = f"""Analyze the French word: "{word}"

    1. First, determine if this is a verb in its infinitive form. If it is NOT a verb, return exactly: 'not a verb'

    2. If it IS a verb, provide ONLY the conjugations in present tense in this format:
    je [conjugation]\n
    tu [conjugation]\n
    il/elle/on [conjugation]\n
    nous [conjugation]\n
    vous [conjugation]\n
    ils/elles [conjugation]\n

    3. Return ONLY the conjugations or 'not a verb' - no explanations, no additional text."""

        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_MODEL
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"Error: {str(e)}"
        
        
    def youtube_french_sentence_generator(self, transcript: str) -> str:
        """
        Generate a numbered list of French sentences from a YouTube transcript.
        
        Args:
            transcript: The YouTube transcript text
            
        Returns:
            A string with numbered French sentences
        """
        prompt = f"""Extract and number the French sentences from the following transcript: {transcript}. Do not modify the sentences, just return them as a numbered list.
        
        Format the output like this do not include any additional text or explanations:
        1. French Sentence one
        2. French Sentence two
        3. French Sentence three"""
        
        try:
            response  = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_TRANSCRIPT_MODEL
            )
            response =  response.choices[0].message.content.strip()
        
            
        except Exception as e:
            return f"Error: {str(e)}"
        
        return response
    
    
    def youtube_english_sentence_generator(self, french_transcript: str) -> str:
        """
        Generate a numbered list of English sentences from a french sentence list.
        
        Args:
            french_transcript: french transcript
            
        Returns:
            A string with numbered English sentences
        """
        prompt = f"""Translate literally of numbered french sentences from {french_transcript} to english numbered sentences list.
                     Maintain the original numbering and structure.
        
        Format the output like this do not include any additional text or explanations:
        1. English Sentence one
        2. English Sentence two
        3. English Sentence three"""
        
        try:
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=GROQ_TRANSCRIPT_MODEL
            )
            response = response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error: {str(e)}"
        
        return response
    
    
    