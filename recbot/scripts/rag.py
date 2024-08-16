from pymongo import MongoClient
from langchain_openai import AzureOpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from openai import AzureOpenAI
import environ
from recbot.scripts.data import MODEL_SHOTS
from datetime import datetime, timedelta
import numpy as np
from numpy.linalg import norm
import pandas as pd
import threading
import queue

class RAG:
    azure_model_embedding_name = 'text-embedding-ada-002'
    azure_model_generate_name = 'gpt-35-turbo'
    shots = MODEL_SHOTS

    def __init__(self):
        env = environ.Env()
        environ.Env.read_env()

        AZURE_OPENAI_API_KEY = env('AZURE_OPENAI_API_KEY')
        AZURE_ENDPOINT = env('AZURE_ENDPOINT')
        AZURE_API_VERSION = env('AZURE_API_VERSION')
        MONGO_FOODREC = env('MONGO_FOODREC')

        self.embedding = AzureOpenAIEmbeddings(model = self.azure_model_embedding_name, api_key= AZURE_OPENAI_API_KEY , azure_endpoint = AZURE_ENDPOINT)
        self.azure_model = AzureOpenAI(azure_endpoint = AZURE_ENDPOINT, api_key= AZURE_OPENAI_API_KEY, api_version = AZURE_API_VERSION)
        self.mongo_client_foodrec = MongoClient(MONGO_FOODREC)
    
    def cosine_similarity(self, collection, city, neighborhood, k, embedding, qeue_result):
        pipeline = [
        {
            '$match': { 
                f'can_be_delivered_to.{city}': {'$in':[neighborhood]}
                }
        },
        {
            '$limit': 1000
        },
        {
            '$project': {
                '_id': 1,
                'text': 1,
                'name': 1,
                'price': 1,
                'restaurant_id': 1,
                'score' : {
                    '$divide':[
                        {
                            '$reduce': {
                                'input': {'$range': [ 0, {'$size': '$embedding' }]},
                                'initialValue': 0,
                                'in': { '$add': [ '$$value', { '$multiply': [ { '$arrayElemAt': [ '$embedding', '$$this' ] }, { '$arrayElemAt': [ embedding, "$$this"]}]}]}
                            }
                        },
                        {
                            '$multiply' : [
                                {
                                    '$sqrt':{
                                        '$reduce': {
                                            'input': {'$range': [ 0, {'$size': '$embedding' }]},
                                            'initialValue': 0,
                                            'in': { '$add': [ '$$value', { '$multiply': [ { '$arrayElemAt': [ '$embedding', '$$this' ] }, { '$arrayElemAt': [ '$embedding', "$$this"]}]}]}
                                        }
                                    }
                                },
                                {   '$sqrt':{
                                        '$reduce': {
                                            'input': {'$range': [ 0, {'$size': '$embedding' }]},
                                            'initialValue': 0,
                                            'in': { '$add': [ '$$value', { '$multiply': [ { '$arrayElemAt': [ embedding, '$$this' ] }, { '$arrayElemAt': [ embedding, "$$this"]}]}]}
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        },
        {'$sort': {'score': -1}},
        {'$limit' : k}
        ]

        result_dish = collection.aggregate(pipeline)
        list_dish = list(result_dish)
        
        qeue_result.put(list_dish)
    
    def retriever_k(self, input: str, k = 10, city = None, neighborhood = None, limit = 0.92):
        """
        database_date = datetime.today()

        if database_date.hour > 9:
            database_date = datetime.today() - timedelta(days = 1)
        else:
            database_date = datetime.today() - timedelta(days = 2)
        
        database_date_name = database_date.strftime('%Y-%m-%d')
        collection_ifood_dish = self.mongo_client_foodrec[database_date_name + '-ifood-webscraping']['dish']
        collection_rappi_dish = self.mongo_client_foodrec[database_date_name + '-rappi-webscraping']['dish']
        """
        embedding = self.azure_model.embeddings.create(input = [input], model=self.azure_model_embedding_name).data[0].embedding

        collection_ifood_dish = self.mongo_client_foodrec['2024-08-07-ifood-webscraping']['dish']
        collection_rappi_dish = self.mongo_client_foodrec['2024-08-07-rappi-webscraping']['dish']

        queue_ifood = queue.Queue()
        queue_rappi = queue.Queue()

        thread_ifood = threading.Thread(target=self.cosine_similarity, args=(collection_ifood_dish, city, neighborhood, 2, embedding, queue_ifood))
        thread_rappi = threading.Thread(target=self.cosine_similarity, args=(collection_rappi_dish, city, neighborhood, 2, embedding, queue_rappi))

        thread_ifood.start()
        thread_rappi.start()

        thread_ifood.join()
        thread_rappi.join()
        
        list_total_dish = queue_ifood.get() + queue_rappi.get()
        if list_total_dish == []:
            return []

        df_results = pd.DataFrame.from_dict(list_total_dish)
        df_results = df_results[df_results['score'] >= limit] 
        df_results = df_results.sort_values(by=['price'], ascending=True)
        df_results = df_results[['text','_id', 'name', 'restaurant_id', 'score']]
        return df_results.to_dict('records')
    
    def get_list_similarity(self, embedding, city, neighborhood):
        """
        database_date = datetime.today()

        if database_date.hour > 9:
            database_date = datetime.today() - timedelta(days = 1)
            database_rappi_name = database_date.strftime('%Y-%m-%d') + '-rappi-webscraping'
        else:
            database_date = datetime.today() - timedelta(days = 2)
            database_rappi_name = database_date.strftime('%Y-%m-%d') + '-rappi-webscraping'
        """
        collection_ifood_dish = self.mongo_client_foodrec['2024-08-07-ifood-webscraping']['dish']
        collection_rappi_dish = self.mongo_client_foodrec['2024-08-07-rappi-webscraping']['dish']

        queue_ifood = queue.Queue()
        queue_rappi = queue.Queue()

        thread_ifood = threading.Thread(target=self.cosine_similarity, args=(collection_ifood_dish, city, neighborhood, 1000, embedding, queue_ifood))
        thread_rappi = threading.Thread(target=self.cosine_similarity, args=(collection_rappi_dish, city, neighborhood, 1000, embedding, queue_rappi))

        thread_ifood.start()
        thread_rappi.start()

        thread_ifood.join()
        thread_rappi.join()
        
        list_total_dish = queue_ifood.get() + queue_rappi.get()
        if list_total_dish == []:
            return []

        df_results = pd.DataFrame.from_dict(list_total_dish)
        df_results = df_results[['text', '_id', 'name', 'restaurant_id', 'score']]
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
            if c['role'] == 'user':
                conversation_history_formated.append({'role':c['role'], 'content':c['content']})
            elif c['role'] == 'assistant':
                conversation_history_formated.append({'role':c['role'], 'content':c['content'] + f" Somente serão apresentadas sugestões que são entregues em {neighborhood}, {city}, não apresente sugestões de pratos para cidade ou bairros diferentes destes."})
            else:
                list_sugestions_history = c['content'].split('; https')
                l_result = ''
                l_sugestions = len(list_sugestions_history)
                for l in range(l_sugestions):
                    new_sugestion = list_sugestions_history[l]
                    if l == 0:
                        l_result = new_sugestion
                    else:
                        l_result += new_sugestion[new_sugestion.find(';')+2:]
                    if l < (l_sugestions - 1):
                        l_result += '. ' 
                conversation_history_formated[-1]['content'] += l_result

        input = conversation_history[-1]['content']
        results_retriever = self.retriever_k(input, 5, city, neighborhood, limit = 0.85)
        sugestions = ' '
        sugestions_prompt = ' '
        for r in results_retriever:
            if sugestions == ' ':
                sugestions = ' Sugestões: '
                sugestions_prompt = ' Sugestões: '
            sugestions = sugestions + r['text'] + '; '
            new_sugestion = r['text']
            new_sugestion = new_sugestion[:new_sugestion.find('; https')]
            sugestions_prompt = sugestions_prompt + new_sugestion + '. '
        
        conversation_history_formated[-1]['content'] += sugestions_prompt
        conversation = self.shots + conversation_history_formated
        results = self.generate(conversation)
        response = results.choices[0].message.content

        while response[-1] != '.' and response[-1] != '!' and response[-1] != '?':
            for i in range(len(response)):
                if response[(-1)*(1+i)] == '.' or response[(-1)*(1+i)] == '!' or response[(-1)*(1+i)] == '?':
                    response = response[0:len(response) - i]
                    break
            last_word_response = response[-5:]
            index_word_ifood = 'https://www.ifood.com.br'.find(last_word_response)
            index_word_rappi = 'https://www.rappi.com.br'.find(last_word_response)

            if index_word_ifood != -1:
                response = response[:-(index_word_ifood + len(last_word_response))]
            elif index_word_rappi != -1:
                response = response[:-(index_word_rappi + len(last_word_response))]


        conversation_history.append({"role":"sugestions","content":sugestions})
        conversation_history.append({"role":"assistant","content":response})
        list_dish_documents = [{'dish_id':str(r['_id']), 'dish_name': r['name'], 'restaurant_id': str(r['restaurant_id']), 'score':r['score']} for r in results_retriever]

        return {"response": conversation_history, "list_dish_documents": list_dish_documents}