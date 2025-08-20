from ast import literal_eval
from core.llm_utils import LLMUtils
from config.settings import GROQ_MODEL


llm_utils = LLMUtils()

def check_translation(original: str, attempt: str, correct: str):
    prompt = f"""/no_think
You are a strict but fair French translation evaluator.

Compare the user's translation to the correct one. Provide:
1. Correct French Translation 
2. A short and concise feedback comment as bullet point (1-2 sentences).
3. A score from 0 to 10 (integer only), based on correctness of users translation compared to correct french sentence.
Return your response in the following JSON format only:
{{
  
  "correct": correct french translation,
  "feedback": "your concise feedback here",
  "score": "your score here"
}}

Now evaluate:

English sentence: "{original}"
User's French translation: "{attempt}"
Correct French translation: "{correct}"

"""
    response = llm_utils.groq_client.chat.completions.create(
            messages=[
             {"role": "user", "content": prompt}],
            model=GROQ_MODEL )
    response = response.choices[0].message.content.strip()
    

    
    try:
        result = literal_eval(response)
        feedback = result.get("feedback", "")
        score = result.get("score", 0)
    except Exception as e:
        feedback = "⚠️ Failed to parse LLM response."
        score = 0
        print(e)
    return feedback, score