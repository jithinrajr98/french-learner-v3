from langchain_ollama import ChatOllama
from typing import List, Dict, Any
from ast import literal_eval
import re, os
from config.settings import GROQ_MODEL
from groq import Groq
from dotenv import load_dotenv
load_dotenv()



class LLMUtils:
    
    def __init__(self):
        """
        Initialize the LLMUtils class with a Groq client.
        """
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))  
    
    def get_french_word_meaning(self, word: str) -> str:
        """
        Get the meaning of a French word using a language model.
        """
        prompt = f"Please provide the meaning of the French word '{word}' in English. Return up to 3 meanings as a single comma seperated list. Do not explain"
        response = self.groq_client.chat.completions.create(
            messages=[
             {"role": "user", "content": prompt}],
            model=GROQ_MODEL )
        
        return response.choices[0].message.content.strip()
    
    
    def extract_missed_words(self, correct: str, attempt: str) -> List[str]:
        """/nothink Identify missing words from user's translation attempt"""
        prompt = f"""
        Compare these French translations:
        Correct: {correct}
        Attempt: {attempt}
        
        Identify which content words (nouns, verbs, adjectives, adverbs) 
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
