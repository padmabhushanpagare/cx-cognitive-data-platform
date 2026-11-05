import os
import json
import psycopg2
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# DB Config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5434")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# 1. Initialize our local LLM
llm = ChatOllama(model="llama3.1", temperature=0, base_url=OLLAMA_BASE_URL)

# 2. Define the QA Rubric Prompt
qa_prompt = PromptTemplate(
    template="""You are an expert BPO Quality Assurance Supervisor. 
Evaluate the following customer interaction based on a 1-5 scale for:
1. Resolution (Did the AI answer the customer's question?)
2. Empathy (Was the AI polite and understanding?)
3. Policy (Did the AI follow the rules, e.g., not giving unauthorized refunds?)

Customer Message: {customer_msg}
AI Response: {ai_response}
Escalated to Human: {escalated}

You must output ONLY a valid JSON object with exactly these keys:
{{
    "resolution_score": <int 1-5>,
    "empathy_score": <int 1-5>,
    "policy_score": <int 1-5>,
    "requires_human_review": <boolean>,
    "qa_feedback": "<string explaining the scores>"
}}
""",
    input_variables=["customer_msg", "ai_response", "escalated"]
)

# Create the chain
qa_chain = qa_prompt | llm | JsonOutputParser()

def evaluate_recent_interactions():
    print("Connecting to database...")
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user="admin", password="cx_secret_password", dbname="cx_platform")
    cursor = conn.cursor()
    
    # Get interactions that haven't been scored yet
    query = """
        SELECT c.id, c.user_message, c.ai_response, c.escalated 
        FROM conversation_logs c
        LEFT JOIN fact_quality_scores q ON c.id = q.log_id
        WHERE q.score_id IS NULL;
    """
    cursor.execute(query)
    logs = cursor.fetchall()
    
    print(f"Found {len(logs)} interactions to evaluate.")
    
    for log in logs:
        log_id, user_msg, ai_msg, escalated = log
        print(f"\nEvaluating Log #{log_id}...")
        
        try:
            # Run the LLM to grade the conversation
            result = qa_chain.invoke({
                "customer_msg": user_msg,
                "ai_response": ai_msg,
                "escalated": escalated
            })
            
            # Calculate overall score
            overall = int((result['resolution_score'] + result['empathy_score'] + result['policy_score']) / 3)
            
            # Save to database
            insert_query = """
                INSERT INTO fact_quality_scores 
                (log_id, overall_score, resolution_score, empathy_score, policy_score, requires_human_review, qa_feedback) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                log_id, overall, result['resolution_score'], result['empathy_score'], 
                result['policy_score'], result['requires_human_review'], result['qa_feedback']
            ))
            conn.commit()
            print(f"✅ Saved QA Score: {overall}/5. Feedback: {result['qa_feedback'][:50]}...")
            
        except Exception as e:
            print(f"❌ Failed to evaluate log #{log_id}: {e}")
            conn.rollback()

    cursor.close()
    conn.close()
    print("\nQA Evaluation Complete.")

if __name__ == "__main__":
    evaluate_recent_interactions()
