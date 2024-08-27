from recbot.src.external_acess.acess_variables import AZURE_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_API_VERSION
from openai import AzureOpenAI

class AzureAPI:
    azure_model_generate_name = 'gpt-35-turbo'
    azure_model_embedding_name = 'text-embedding-ada-002'

    def __init__(self) -> None:
        pass

    def get_client(self):
        return AzureOpenAI(azure_endpoint = AZURE_ENDPOINT, api_key= AZURE_OPENAI_API_KEY, api_version = AZURE_API_VERSION)

    def chatCompletion(self, client: AzureOpenAI, messages: list, temperature=0.7, max_tokens=300, top_p=0.95, frequency_penalty=0, presence_penalty=0):
        return client.chat.completions.create(model = self.azure_model_generate_name, messages = messages, temperature=temperature, max_tokens=max_tokens, top_p=top_p, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty)
    
    def embeddingGenerate(self, client: AzureOpenAI, input: list):
        return client.embeddings.create(input = input, model=self.azure_model_embedding_name)

