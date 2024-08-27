from recbot.src.model.rag import RAG
from recbot.src.model.standard import Standard
from recbot.src.request.request_azure import RequestAzure

class ChatOutput:
    def __init__(self):
        self.rag = RAG()
        self.standard = Standard()
        self.request_azure = RequestAzure()

    def converstion_formated(self, conversation):
        conversation_history_formated = []
        for c in conversation:
            if c['role'] == 'user' or c['role'] == 'assistant':
                conversation_history_formated.append({'role':c['role'], 'content':c['content']})
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
        return conversation_history_formated
    
    def str_sugestions(self, results_retriever):
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
        return [sugestions, sugestions_prompt]
    
    def clean_response(self, response):
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
        return response
    
    def bot_response(self, conversation_history: list, city: str, neighborhood: str):
        input = conversation_history[-1]['content']
        embedding = self.request_azure.embedding(input).data[0].embedding
        out_retriever = self.rag.retriever(embedding, city, neighborhood)
        sugestions = self.str_sugestions(out_retriever)
        prompt_sugestions = sugestions[1]
        conversation_history_formated = self.converstion_formated(conversation_history)
        conversation_history_formated[-1]['content'] += prompt_sugestions
        result = self.rag.generate(conversation_history_formated, city, neighborhood) if prompt_sugestions != ' ' else self.standard.generate(conversation_history_formated, city, neighborhood)
        response = result.choices[0].message.content
        response = self.clean_response(response)
        conversation_history.append({"role":"sugestions","content":sugestions[0]})
        conversation_history.append({"role":"assistant","content":response})
        list_dish_documents = [{'dish_id':str(r['_id']), 'dish_name': r['name'], 'restaurant_id': str(r['restaurant_id']), 'score':r['score']} for r in out_retriever]

        return {"response": conversation_history, "list_dish_documents": list_dish_documents}

    def recomender_response(self, embedding, city: str, neighborhood: str):
        return self.rag.retriever(embedding, city, neighborhood, score= False, filter_by = 'score', ascending=False, k = 1000)



    