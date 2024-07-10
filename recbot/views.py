from django.template import loader
from django.http import HttpResponse, JsonResponse
from recbot.scripts.rag import RAG

rag = RAG()

def recbotResponse(request):
    text = request.GET.get('text')
    response = rag.output(text)
    restaurants = [{"_id":r[0].metadata["_id_restaurant"],"id_dish":str(r[0].metadata["_id"]),"score":r[1]} for r in response["list_dish_documents"]]
    dict_response = {"response" : response["response"], "restaurants":restaurants}
    return JsonResponse(dict_response)

def recbot(request):
    template = loader.get_template('starter.html')
    return HttpResponse(template.render())
