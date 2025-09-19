from langchain_ollama import ChatOllama
from settings.loader import get



def llm():
    """Helper function to create a ChatOllama instance with config values."""
    model = get("MODEL_NAME")
    temperature = get("TEMPERATURE")
    # reasoning = get("REASONING")
    return ChatOllama(model=model, 
                      temperature=temperature, )
                    #   reasoning=reasoning)

