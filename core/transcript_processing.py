from pathlib import Path
from typing import List, Tuple
import random
from config.settings import TRANSCRIPT_EN, TRANSCRIPT_FR
import re
from urllib.parse import urlparse, parse_qs
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from config.settings import TRANSCRIPT_YOUTUBE


class TranscriptManager:
    
    def __init__(self):
        
        self.english_sentences = self._load_transcript(TRANSCRIPT_EN)
        self.french_sentences = self._load_transcript(TRANSCRIPT_FR)
        

    def _load_transcript(self, file_path: Path) -> List[str]:
        """Load and parse transcript file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [
                    line.strip().split(". ", 1)[1] 
                    for line in f 
                    if ". " in line and len(line.split(". ", 1)) > 1
                ]
        except FileNotFoundError:
            raise Exception(f"Transcript file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error loading transcript: {str(e)}")
        
    def load_youtube_transcript(self,file_path:Path) -> str:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return content
        
    def _validate_pairs(self):
        """Verify English and French transcripts have matching lengths"""
        if len(self.english_sentences) != len(self.french_sentences):
            raise ValueError(
                f"Mismatched transcript lengths: "
                f"English={len(self.english_sentences)}, "
                f"French={len(self.french_sentences)}"
            )
        
    def get_random_pair(self) -> Tuple  :
        # Initialize index list on first run
        if 'shuffled_indices' not in st.session_state or not st.session_state.shuffled_indices:
            indices = list(range(len(self.english_sentences)))
            random.shuffle(indices)
            st.session_state.shuffled_indices = indices
            st.session_state.index_pointer = 0

        idx = st.session_state.shuffled_indices[st.session_state.index_pointer]
        st.session_state.index_pointer += 1

        # Reset when all sentences are used
        if st.session_state.index_pointer >= len(self.english_sentences):
            st.session_state.shuffled_indices = []
            st.session_state.index_pointer = 0

        return self.english_sentences[idx], self.french_sentences[idx]
    


    def extract_transcript(self, video_url: str):
    
        # Extract video ID from different YouTube URL formats
        parsed_url = urlparse(video_url)
        
        if parsed_url.hostname in ['youtube.com', 'www.youtube.com', 'm.youtube.com']:
            if parsed_url.path == '/watch':
                video_id = parse_qs(parsed_url.query).get('v', [None])[0]
            elif parsed_url.path.startswith('/embed/'):
                video_id = parsed_url.path.split('/')[2]
            elif parsed_url.path.startswith('/v/'):
                video_id = parsed_url.path.split('/')[2]
        elif parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path[1:]  # Remove the leading slash
        else:
            raise ValueError("Invalid YouTube URL")
        
        if not video_id:
            raise ValueError("Could not extract video ID from URL")
        
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id, languages=["fr"])
        sentences = []
        for snippet in fetched_transcript:
            sentences.append(snippet.text)
        transcript = " ".join(sentences)
        try:
            with open(TRANSCRIPT_YOUTUBE, "w", encoding="utf-8") as file:
                file.write(transcript)
                print(f"Transcript saved to {TRANSCRIPT_YOUTUBE}")
        except IOError as e:
            print(f"An error occurred while writing to the file: {e}")


transcript_manager = TranscriptManager()