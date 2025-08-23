from supabase import create_client, Client
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from core.llm_utils import LLMUtils
load_dotenv()

class SupabaseDB:
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_API_KEY')
        self.supabase = create_client(url, key)
        self.llm_utils =  LLMUtils()

    def save_missing_words(self, words):
        """Save missing words with meanings"""
        try:
            for word in words:
                if len(word.strip()) <= 3:
                    continue
                
                # Check if word already exists
                existing = self.supabase.table('missing_words').select('word').eq('word', word).execute()
                
                if not existing.data:
                    # Get meaning using LLM utility
                    meaning = self.llm_utils.get_french_word_meaning(word)
                    
                    # Insert word with error handling
                    try:
                        response = self.supabase.table('missing_words').insert({
                            'word': word, 
                            'meaning': meaning
                        }).execute()
                        
                        # Check for errors in the response
                        if hasattr(response, 'error') and response.error:
                            print(f"Error inserting word {word}: {response.error}")
                    
                    except Exception as insert_error:
                        print(f"Insertion error for word {word}: {insert_error}")
    
        except Exception as e:
            print(f"Error in save_missing_words: {e}")

    def save_score(self, sentence, user_translation, score):
        """Save translation score"""
        try:
            self.supabase.table('translation_scores').insert({
                'sentence': sentence,
                'user_translation': user_translation,
                'score': score
            }).execute()
        except Exception as e:
            print(f"Error saving score: {e}")

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

    def get_score_history(self):
        """Get all score history"""
        try:
            response = self.supabase.table('translation_scores').select('*').order('checked_on').execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error fetching score history: {e}")
            return pd.DataFrame()

    def get_daily_scores(self):
        """Get average scores grouped by day"""
        try:
            # Use the specific function we created
            response = self.supabase.rpc('get_daily_scores').execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error fetching daily scores: {e}")
            return pd.DataFrame()

    def get_weekly_progress(self):
        """Get weekly progress data"""
        try:
            response = self.supabase.rpc('get_weekly_progress').execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error fetching weekly progress: {e}")
            return pd.DataFrame()

    def get_score_statistics(self):
        """Get overall score statistics"""
        try:
            response = self.supabase.rpc('get_score_statistics').execute()
            if response.data and len(response.data) > 0:
                result = response.data[0]
                return {
                    'total_attempts': result.get('total_attempts', 0),
                    'overall_avg': round(result.get('overall_avg', 0), 2) if result.get('overall_avg') else 0,
                    'min_score': result.get('min_score', 0),
                    'max_score': result.get('max_score', 0),
                    'days_active': result.get('days_active', 0)
                }
            return {
                'total_attempts': 0,
                'overall_avg': 0,
                'min_score': 0,
                'max_score': 0,
                'days_active': 0
            }
        except Exception as e:
            print(f"Error fetching score statistics: {e}")
            return {
                'total_attempts': 0,
                'overall_avg': 0,
                'min_score': 0,
                'max_score': 0,
                'days_active': 0
            }