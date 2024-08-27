from recbot.src.external_acess.azure_api import AzureAPI

class RequestAzure:
    def __init__(self):
        self.api = AzureAPI()
    
    def completion(self, messages: list, temperature=0.7, max_tokens=300, top_p=0.95, frequency_penalty=0, presence_penalty=0):
        client = self.api.get_client()
        return self.api.chatCompletion(client=client, messages=messages, temperature=temperature, max_tokens=max_tokens, top_p=top_p, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty)
    
    def embedding(self, input: str):
        client = self.api.get_client()
        return self.api.embeddingGenerate(client=client, input=[input])