from django.template import loader
from django.http import HttpResponse, JsonResponse
from recbot.scripts.rag import RAG



def recbotResponse(request):
    text = request.GET.get('text')
    response = 'oi'
    dict_response = {"response" : response}
    return JsonResponse(dict_response)

def recbot(request):
    template = loader.get_template('starter.html')
    return HttpResponse(template.render())
