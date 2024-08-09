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
import time

class RAG:
    azure_model_embedding_name = 'text-embedding-ada-002'
    azure_model_generate_name = 'gpt-4'
    shots = MODEL_SHOTS

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
        self.embedding = AzureOpenAIEmbeddings(model = self.azure_model_embedding_name, api_key= AZURE_OPENAI_API_KEY , azure_endpoint = AZURE_ENDPOINT)
        self.vector_search = MongoDBAtlasVectorSearch( collection = self.collection, embedding = self.embedding, index_name = MONGO_VECTOR_INDEX_NAME)
        self.vector_search_rappi = MongoDBAtlasVectorSearch( collection = self.collection_rappi, embedding = self.embedding, index_name = MONGO_VECTOR_INDEX_NAME)
        self.azure_model = AzureOpenAI(azure_endpoint = AZURE_ENDPOINT, api_key= AZURE_OPENAI_API_KEY, api_version = AZURE_API_VERSION)
        self.mongo_client_foodrec = MongoClient(MONGO_FOODREC)
    
    def retriever_k(self, input: str, k = 10, city = None, neighborhood = None):
        database_date = datetime.today()
        
        #database_rappi_name = 'TESTE-2024-07-23-rappi-webscraping'

        if database_date.hour > 9:
            database_date = datetime.today() - timedelta(days = 1)
            database_rappi_name = database_date.strftime('%Y-%m-%d') + '-rappi-webscraping'
        else:
            database_date = datetime.today() - timedelta(days = 2)
            database_rappi_name = database_date.strftime('%Y-%m-%d') + '-rappi-webscraping'
        
        collection_rappi_dish = self.mongo_client_foodrec[database_rappi_name]['dish']
        
        query = {}
        if city != None and neighborhood != None:
            query = { 'can_be_delivered_to.{}'.format(city): {'$in':[neighborhood]}}
        
        list_collection_rappi_dish = list(collection_rappi_dish.find(query).limit(200))
        start_time = time.time()
        
        embedding = self.azure_model.embeddings.create(input = [input], model=self.azure_model_embedding_name).data[0].embedding

        for l in list_collection_rappi_dish:
            embedding_array = np.array(l['embedding'])
            score = np.dot(embedding, embedding_array) / (norm(embedding) * norm(embedding_array))
            l['score'] = score

        df_results = pd.DataFrame.from_dict(list_collection_rappi_dish)
        df_results = df_results[['text','_id', 'name', 'restaurant_id', 'score']]
        df_results = df_results.sort_values(by=['score'], ascending=False)
        df_results = df_results[:][:k]
        return df_results.to_dict('records')

    def retriever(self, input: str):
        k = 3
        result_ifood = self.vector_search.similarity_search_with_score(input, k)
        result_rappi = self.vector_search_rappi.similarity_search_with_score(input, k)

        return result_ifood + result_rappi
    
    def get_list_similarity(self, embedding, city, neighborhood):
        database_date = datetime.today()

        if database_date.hour > 9:
            database_date = datetime.today() - timedelta(days = 1)
            database_rappi_name = database_date.strftime('%Y-%m-%d') + '-rappi-webscraping'
        else:
            database_date = datetime.today() - timedelta(days = 2)
            database_rappi_name = database_date.strftime('%Y-%m-%d') + '-rappi-webscraping'

        collection_rappi_dish = self.mongo_client_foodrec[database_rappi_name]['dish']
        myquery = { 'can_be_delivered_to.{}'.format(city): {'$in':[neighborhood]}}
        list_collection_rappi_dish = list(collection_rappi_dish.find(myquery).limit(200))

        for l in list_collection_rappi_dish:
            embedding_array = np.array(l['embedding'])
            score = np.dot(embedding, embedding_array) / (norm(embedding) * norm(embedding_array))
            l['score'] = score

        df_results = pd.DataFrame.from_dict(list_collection_rappi_dish)
        df_results = df_results[['_id', 'name', 'restaurant_id', 'score']]
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
    
    def output(self, conversation_history: list, city, neighborhood):
        conversation_history_formated = []
        for c in conversation_history:
            if c['role'] == 'user' or c['role'] == 'assistant':
                conversation_history_formated.append({'role':c['role'], 'content':c['content']})
            else:
                conversation_history_formated[-1]['content'] += c['content']

        input = conversation_history[-1]['content']
        results_retriever = self.retriever_k(input, 5, city, neighborhood)
        THRESHOLD_MIN = 0.80
        sugestions = ' '
        for i in range(3):
            r = results_retriever[i]
            if r['score'] > THRESHOLD_MIN:
                if sugestions == ' ':
                    sugestions = ' Sugestões: '
                sugestions = sugestions + r['text'] + '; '
        
        conversation_history_formated[-1]['content'] += sugestions
        conversation = self.shots + conversation_history_formated
        results = self.generate(conversation)
        response = results.choices[0].message.content

        if response[-1] != '.' and response[-1] != '!' and response[-1] != '?':
            for i in range(len(response)):
                if response[(-1)*(1+i)] == '.' or response[(-1)*(1+i)] == '!' or response[(-1)*(1+i)] == '?':
                    response = response[0:len(response) - i]
                    break

        conversation_history.append({"role":"sugestions","content":sugestions})
        conversation_history.append({"role":"assistant","content":response})
        list_dish_documents = [{'dish_id':str(r['_id']), 'dish_name': r['name'], 'restaurant_id': str(r['restaurant_id']), 'score':r['score']} for r in results_retriever]

        return {"response": conversation_history, "list_dish_documents": list_dish_documents}



        
        