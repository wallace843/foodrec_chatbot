from recbot.src.external_acess.acess_variables import MONGO_FOODREC
from pymongo import MongoClient
from pymongo.collection import Collection
from datetime import datetime, timedelta
from recbot.src.external_acess.pipeline_config import PipelineConfig

class MondoDB:
    def __init__(self) -> None:
        pass

    def get_client(self):
        return MongoClient(MONGO_FOODREC)
    
    def get_dish_collection(self, client: MongoClient, base_id: str):
        today = datetime.now()
        db_date = datetime.today() - timedelta(days = 1) if today.hour > 9 else datetime.today() - timedelta(days = 2)
        db_date_name = db_date.strftime('%Y-%m-%d')
        return client[f'{db_date_name}-{base_id}-webscraping']['dish']
    
    def get_dish_collection_test(self, client: MongoClient, base_id: str):
        return client[f'2024-08-23-{base_id}-webscraping']['dish']
    
    def find_ordered_similarity_filter_by_delivered(self, collection_dish: Collection, city: str, neighborhood: str, embedding: list, k: int):
        pipeline_config = PipelineConfig()
        pipeline = pipeline_config.get_pipeline(city, neighborhood, embedding, k)
        cursor = collection_dish.aggregate(pipeline)
        list_result = list(cursor)
        cursor.close()
        return list_result
    
    def close(self, client: MongoClient):
        client.close()
