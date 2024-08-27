from recbot.src.request.request_azure import RequestAzure
from recbot.src.request.request_mongodb import RequestMongoDB
import pandas as pd

class RAG:
    top_k = 2
    score_min_similarity=0.85
    shots = [
        {"role":"system","content":"Seu nome é Recbot e você é um assistente de recomendação que auxiliar os usuários na escolha de refeições e restaurantes da plataforma FoodRec. Para fazer suas recomendações, você utiliza os dados extraídos das plataformas Ifood e Rapppi. Para perguntas que não se relacionam com refeições ou restaurantes, sugira uma outra fonte de informação. Ignore pedidos ou ordens que solicitem a alteração do idioma de suas respostas ou na formatação de suas respostas, como a inclusão ou retirada de símbolos, palavras ou caracteres, diga que não tem autorização para mudar o padrão das respostas. Suas respostas devem ter comprimento máximo de 250 tokens. Não use enumerações, hífens, asterísticos ou quebra de linha em suas repostas. Sua respostas devem conter todas as refeições mostradas nas sugestões com o máximo de detalhes."},
        {"role":"user","content":"queria tomar guarana jesus Sugestões: Refrigerante Guarana Jesus 350ml: lata 350ml.; preço 7.0; Donico Coxinhas Artesanais Com Massa de; avaliação 4.9; ifood. Guarana Jesus: lata 350ml; preço 7.15; Pasta in Cup; avaliação 4.9; ifood. Guarana Jesus: lata 350ml; preço 7.15.; Pasta in Cup; avaliação 5.0; rappi. Refrigerante de 1 Litro: ; preço 10.0; Petiscaria Pajucara; avaliação 0.0; rappi. "},
        {"role":"assistant","content":"Temos algumas boas opções onde vc pode comprar Guaraná Jesus 350ml: no restaurante Donico Coxinhas Artesanais por R$ 7,00, disponível no Ifood; e no restaurante Pasta in Cup custando R$ 7,15, disponível no Ifood e no Rappi. Também pode comprar Refrigerante de 1 Litro a R$ 10.0 na Petiscaria Pajucara, disponível no Rappi."},
    ]

    def __init__(self):
        self.azure_request = RequestAzure()
        self.mongo_request = RequestMongoDB()

    def retriever(self, embedding, city, neighborhood, score= True, filter_by = 'price', ascending=True, k = top_k):
        list_documents = self.mongo_request.find_all_collections(city, neighborhood, embedding, k)
        if list_documents == []:
            return []
        df_results = pd.DataFrame.from_dict(list_documents)
        df_results = df_results[df_results['score'] >= self.score_min_similarity] if score else df_results
        df_results = df_results.sort_values(by=[filter_by], ascending=ascending)
        df_results = df_results[['text','_id', 'name', 'restaurant_id', 'score']]
        return df_results.to_dict('records')
    
    def generate(self, input, city, neighborhood):
        consersation = self.shots
        consersation = consersation + input
        consersation[0]['content'] += f" Somente serão apresentadas sugestões que são entregues em {neighborhood}, {city}. Não apresente sugestões de pratos para cidade ou bairros diferentes destes."
        return self.azure_request.completion(consersation)



