from django.template import loader
from django.http import HttpResponse, JsonResponse
from recbot.scripts.rag import RAG

rag = RAG()

def recbotResponse(request):
    text = request.GET.get('text')
    response = rag.output(text)
    dict_response = {"response" : response}
    return JsonResponse(dict_response)

def recbot():
    template = loader.get_template('starter.html')
    return HttpResponse(template.render())
