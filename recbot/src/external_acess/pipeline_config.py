class PipelineConfig:
    def reduce_statement(self, embedding_1, embedding_2):
        return {
            '$reduce': {
                'input': {
                    '$range': [
                        0,
                        {
                            '$size': '$embedding'
                        }
                    ]
                },
                'initialValue': 0,
                'in': {
                    '$add': [
                        '$$value', {
                            '$multiply': [
                                {
                                    '$arrayElemAt': [
                                        embedding_1,
                                        '$$this'
                                    ]
                                },
                                {
                                    '$arrayElemAt':[
                                        embedding_2,
                                        "$$this"
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        }
    
    def cosine_similarity(self, embedding: list):
        return{
            '$divide':[
                self.reduce_statement('$embedding', embedding),
                {
                    '$multiply' : [
                        {
                            '$sqrt':self.reduce_statement('$embedding', '$embedding')
                        },
                        {
                            '$sqrt':self.reduce_statement(embedding, embedding)
                        }
                    ]
                }
            ]
        }
    
    def get_pipeline(self, city: str, neighborhood: str, embedding: list, k: int):
        if k > 1000:
            k = 1000
        return[
            {
                '$match':{
                    f'can_be_delivered_to.{city}': {
                        '$in':[neighborhood]
                    }
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
                    'score' : self.cosine_similarity(embedding)
                }
            },
            {
                '$sort': {
                    'score': -1
                }
            },
            {
                '$limit' : k
            }
        ]