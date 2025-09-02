from ast import literal_eval
from core.llm_utils import LLMUtils
from config.settings import GROQ_MODEL, GROQ_TRANSCRIPT_MODEL, GROQ_EVAL_MODEL, GROQ_SCORE_MODEL
import json
import re

llm_utils = LLMUtils()

def check_translation(original: str, attempt: str, correct: str):
    prompt = f"""/no_think
You are a strict but fair French translation evaluator.

Compare the user's translation to the correct one. Provide:
1. Correct French Translation 
2. give precise and concise feedback explaining 3 critical errors committed. Each error should be seperate sentence.
3. strictly follow this JSON format without any additional text or explanations:
{{
  
  "correct": correct french translation,
  "feedback": "your concise feedback here",
}}

Now evaluate:

English sentence: "{original}"
User's French translation: "{attempt}"
Correct French translation: "{correct}"

"""
    response = llm_utils.groq_client.chat.completions.create(
            messages=[
             {"role": "user", "content": prompt}],
            model=GROQ_EVAL_MODEL )
    response = response.choices[0].message.content.strip()
    
    try:
        result = literal_eval(response)
        print(f"LLM Response: {result}")
        feedback = result.get("feedback", "")
        feedback_sentences = feedback.split(".")
        feedback = "\n".join([f"• {sentence}" for sentence in feedback_sentences if sentence])
        # Get the first sentence of feedback
    except Exception as e:
        feedback = "⚠️ Failed to parse LLM response."
        print(e)
    return feedback



def scorer( attempt: str, correct: str) -> int:
    """
    Evaluates a French translation attempt against the correct translation.
    
    Args:
        attempt: User's French translation attempt
        correct: The correct French translation
        
    Returns:
        Integer score from 0 to 10
    """
    prompt = f"""You are a strict but fair French translation evaluator.
    
    Please evaluate the user's French translation and provide a score from 0 to 10 (integer only).
    Base your score on the correctness of the user's translation compared to both the original English sentence and the correct French translation.
    
    Consider:
    - Grammar accuracy
    - Vocabulary correctness
    - Meaning preservation
    - Natural French expression
    - ignore minor punctuation or accent errors
    
    Respond with only a JSON object in this format:
    {{"score": <integer_between_0_and_10>}}
    
    User's French translation: "{attempt}"
    Correct French translation: "{correct}"
    """
    
    try:
        response = llm_utils.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=GROQ_SCORE_MODEL,
        )
        
        response_content = response.choices[0].message.content.strip()
        print(f"LLM eval Response: {response_content}")
        
        # Try to extract JSON score
        try:
            # First try to parse as JSON
            result = json.loads(response_content)
            score = result.get("score")
        except json.JSONDecodeError:
            # Fallback: try to extract number with regex
            score_match = re.search(r'"score":\s*(\d+)', response_content)
            if score_match:
                score = int(score_match.group(1))
            else:
                # Last resort: extract any number from the response
                number_match = re.search(r'\b(\d+)\b', response_content)
                score = int(number_match.group(1)) if number_match else 5
        
        # Ensure score is within valid range
        score = max(0, min(10, int(score)))
        return score
        
    except Exception as e:
        print(f"Error in scorer function: {e}")
        return 5  # Return neutral score on error
    
    

