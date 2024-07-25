from pymongo import MongoClient
from langchain_openai import AzureOpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from openai import AzureOpenAI
import tiktoken
import environ
from recbot.scripts.data import MODEL_SHOTS
from datetime import datetime, timedelta
import numpy as np
from numpy.linalg import norm
import pandas as pd

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
        MONGO_COLECTION_NAME_RAPPI = env('MONGO_COLECTION_NAME_RAPPI')
        MONGO_VECTOR_INDEX_NAME = env('MONGO_VECTOR_INDEX_NAME')
        AZURE_OPENAI_API_KEY = env('AZURE_OPENAI_API_KEY')
        AZURE_ENDPOINT = env('AZURE_ENDPOINT')
        AZURE_API_VERSION = env('AZURE_API_VERSION')
        MONGO_FOODREC = env('MONGO_FOODREC')

        mongo_client = MongoClient(MONGO_URI)
        self.collection = mongo_client[MONGO_DATABASE_NAME][MONGO_COLECTION_NAME]
        self.collection_rappi = mongo_client[MONGO_DATABASE_NAME][MONGO_COLECTION_NAME_RAPPI]
        embedding = AzureOpenAIEmbeddings(model = self.azure_model_embedding_name, api_key= AZURE_OPENAI_API_KEY , azure_endpoint = AZURE_ENDPOINT)
        self.vector_search = MongoDBAtlasVectorSearch( collection = self.collection, embedding = embedding, index_name = MONGO_VECTOR_INDEX_NAME)
        self.vector_search_rappi = MongoDBAtlasVectorSearch( collection = self.collection_rappi, embedding = embedding, index_name = MONGO_VECTOR_INDEX_NAME)
        self.azure_model = AzureOpenAI(azure_endpoint = AZURE_ENDPOINT, api_key= AZURE_OPENAI_API_KEY, api_version = AZURE_API_VERSION)
        self.mongo_client_foodrec = MongoClient(MONGO_FOODREC)
    
    def retriever_1000(self, input: str):
        k = 1000
        result_ifood_1000 = self.vector_search.similarity_search_with_score(input, k)
        result_rappi_1000 = self.vector_search_rappi.similarity_search_with_score(input, k)

        return result_ifood_1000 + result_rappi_1000

    def retriever(self, input: str):
        k = 3
        result_ifood = self.vector_search.similarity_search_with_score(input, k)
        result_rappi = self.vector_search_rappi.similarity_search_with_score(input, k)

        return result_ifood + result_rappi
    
    def get_list_similarity(self, embedding, city, neighborhood):
        database_date = datetime.today()
        
        database_rappi_name = 'TESTE-2024-07-23-rappi-webscraping'

        """
        if database_date.hour > 13:
            database_rappi_name = database_date.strftime('%Y-%m-%d') + '-rappi-webscraping'
        else:
            database_date = datetime.today() - timedelta(days = 1)
            database_rappi_name = database_date.strftime('%Y-%m-%d') + '-rappi-webscraping'
        """

        print(self.mongo_client_foodrec.list_database_names())
        collection_rappi_dish = self.mongo_client_foodrec[database_rappi_name]['dish']
        myquery = { 'can_be_delivered_to.{}'.format(city): {'$in':[neighborhood]}} 
        list_collection_rappi_dish = list(collection_rappi_dish.find(myquery))

        for l in list_collection_rappi_dish:
            embedding_array = np.array(l['embedding'])
            score = np.dot(embedding, embedding_array) / (norm(embedding) * norm(embedding_array))
            l['score'] = score

        df_results = pd.DataFrame.from_dict(list_collection_rappi_dish)
        df_results = df_results[['_id', 'restaurant_id', 'score']]
        df_results = df_results.sort_values(by=['score'], ascending=False)
        
        return df_results.to_dict('records')

    
    def generate(self, input: list):
        model = self.azure_model_generate_name
        messages = input
        temperature=0.7
        max_tokens=300
        top_p=0.95
        frequency_penalty=0
        presence_penalty=0
        stop=None
        return self.azure_model.chat.completions.create(model = model, messages = messages, temperature=temperature, max_tokens=max_tokens, top_p=top_p, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty, stop=stop)
    
    def output(self, input):
        results = self.retriever(input)
        
        THRESHOLD_MIN = 0.912
        sugestions = ' '
        for r in results:
            if r[1] > THRESHOLD_MIN:
                if sugestions == ' ':
                    sugestions = ' Sugestões: '
                sugestions = sugestions + r[0].page_content + '; '

        results_1000 = self.retriever_1000(input)

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

        return {"response": response, "list_dish_documents": results_1000}



        
        