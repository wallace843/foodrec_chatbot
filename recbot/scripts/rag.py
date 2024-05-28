from pymongo import MongoClient
from langchain_openai import AzureOpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from openai import AzureOpenAI
import tiktoken
import environ
from recbot.scripts.data import MODEL_SHOTS


class RAG:
    azure_model_embedding_name = 'text-embedding-ada-002'
    azure_model_generate_name = 'gpt-4'
    conversation = MODEL_SHOTS

    def __init__(self):
        env = environ.Env()
        environ.Env.read_env()

        MONGO_URI = env('MONGO_URI')
        MONGO_DATABASE_NAME = env('MONGO_DATABASE_NAME')
        MONGO_COLECTION_NAME = env('MONGO_COLECTION_NAME')
        MONGO_VECTOR_INDEX_NAME = env('MONGO_VECTOR_INDEX_NAME')
        AZURE_OPENAI_API_KEY = env('AZURE_OPENAI_API_KEY')
        AZURE_ENDPOINT = env('AZURE_ENDPOINT')
        AZURE_API_VERSION = env('AZURE_API_VERSION')

        mongo_client = MongoClient(MONGO_URI)
        collection = mongo_client[MONGO_DATABASE_NAME][MONGO_COLECTION_NAME]
        embedding = AzureOpenAIEmbeddings(model = self.azure_model_embedding_name, api_key= AZURE_OPENAI_API_KEY , azure_endpoint = AZURE_ENDPOINT)
        self.vector_search = MongoDBAtlasVectorSearch( collection = collection, embedding = embedding, index_name = MONGO_VECTOR_INDEX_NAME)
        
        self.azure_model = AzureOpenAI(azure_endpoint = AZURE_ENDPOINT, api_key= AZURE_OPENAI_API_KEY, api_version = AZURE_API_VERSION)

    def retriever(self, input: str):
        k = 3
        return self.vector_search.similarity_search_with_score(input, k)
    
    def generate(self, input: list):
        model = self.azure_model_generate_name
        messages = input
        temperature=0.7
        max_tokens=150
        top_p=0.95
        frequency_penalty=0
        presence_penalty=0
        stop=None
        return self.azure_model.chat.completions.create(model = model, messages = messages, temperature=temperature, max_tokens=max_tokens, top_p=top_p, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty, stop=stop)
    
    def output(self, input):
        results = self.retriever(input)
        
        THRESHOLD_MIN = 0.92
        sugestions = ' '
        for r in results:
            if r[1] > THRESHOLD_MIN:
                sugestions = sugestions + r[0].page_content + ' '

        input_generate = input + sugestions
        self.conversation.append({"role":"user","content":input_generate})
        results = self.generate(self.conversation)
        response = results.choices[0].message.content

        if response[-1] != '.' and response[-1] != '!' and response[-1] != '?':
            for i in range(len(response)):
                if response[(-1)*(1+i)] == '.' or response[(-1)*(1+i)] == '!' or response[(-1)*(1+i)] == '?':
                    response = response[0:len(response) - i]
                    break

        self.conversation.append({"role":"assistant","content":response})

        return response



        
        