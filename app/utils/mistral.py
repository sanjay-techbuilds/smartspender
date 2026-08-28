import ollama
import json

def query_mistral(user_input):
    """
    Processes the user's voice command using Mistral 7B and returns the AI response.
    
    Args:
        user_input (str): The transcribed voice command.
    
    Returns:
        str: The AI's response based on the user's command.
    """
    try:
        system_prompt = """You are an AI assistant for SmartSpender, a voice-controlled expense tracker.
        You help users manage expenses by understanding commands related to:
        - Adding an expense (date, category, amount, description)
        - Searching expenses
        - Generating reports
        - Providing smart expense suggestions.
        Always return responses in a clear and structured format.
        """

        query_prompt = f"User said: {user_input}\n\nRespond concisely as an AI assistant."

        response = ollama.chat(
            model="mistral",
            messages=[{"role": "system", "content": system_prompt}, 
                      {"role": "user", "content": query_prompt}]
        )

        if response and "message" in response:
            return response["message"]["content"].strip()

        return "I couldn't process that request. Please try again."

    except Exception as e:
        print(f"❌ Error querying Mistral: {e}")
        return "There was an issue processing your command."

