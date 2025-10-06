from langchain_ollama import ChatOllama
from settings.loader import get



def llm():
    """Helper function to create a ChatOllama instance with config values."""
    model = get("MODEL_NAME")
    temperature = get("TEMPERATURE")
    # base_url = get("BASE_URL")  when working with docker container
    reasoning = get("REASONING")
    return ChatOllama(model=model, 
                      temperature=temperature,
                      num_gpu=1,
                      num_thread=8,)
                      # base_url=base_url)
                      # reasoning=reasoning)

