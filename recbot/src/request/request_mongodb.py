from recbot.src.external_acess.mongo_db import MondoDB
import threading
import queue

class RequestMongoDB:
    def __init__(self):
        self.db = MondoDB()

    def task_find(self, client, id_collection, queue: queue, city: str, neighborhood: str, embedding: list, k: int):
        collection = self.db.get_dish_collection_test(client, id_collection)
        return queue.put(self.db.find_ordered_similarity_filter_by_delivered(collection, city, neighborhood, embedding, k))

    def find_all_collections(self, city: str, neighborhood: str, embedding: list, k: int):
        client = self.db.get_client()
        
        queue_ifood = queue.Queue()
        queue_rappi = queue.Queue()

        thread_ifood = threading.Thread(target=self.task_find, args=(client, 'ifood', queue_ifood, city, neighborhood, embedding, k))
        thread_rappi = threading.Thread(target=self.task_find, args=(client, 'rappi', queue_rappi, city, neighborhood, embedding, k))

        thread_ifood.start()
        thread_rappi.start()

        thread_ifood.join()
        thread_rappi.join()

        self.db.close(client)

        return queue_ifood.get() + queue_rappi.get()










    

    