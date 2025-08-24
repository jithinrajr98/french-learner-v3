from ast import literal_eval
from core.llm_utils import LLMUtils
from config.settings import GROQ_MODEL, GROQ_TRANSCRIPT_MODEL


llm_utils = LLMUtils()

def check_translation(original: str, attempt: str, correct: str):
    prompt = f"""/no_think
You are a strict but fair French translation evaluator.

Compare the user's translation to the correct one. Provide:
1. Correct French Translation 
2. give precise feedback explaining errors committed.
3. A score from 0 to 10 (integer only), based on correctness of users translation compared to english sentence.
4. While scoring, ignore any minor punctuation or accent errors, focus on the overall meaning and structure.
5. Do not include any additional text or explanations outside the JSON format.
stricyly follow this JSON format without any additional text or explanations:
{{
  
  "correct": correct french translation,
  "feedback": "your concise feedback here",
  "score": "your score here  as integer between 0 and 10"
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
    print(f"LLM eval Response: {response}")
    

    
    try:
        result = literal_eval(response)
        print(f"LLM Response: {result}")
        feedback = result.get("feedback", "")
        score = result.get("score", 0)
    except Exception as e:
        feedback = "⚠️ Failed to parse LLM response."
        score = 0
        print(e)
    return feedback, score