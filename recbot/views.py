import json
from django.template import loader
from django.http import HttpResponse, JsonResponse
from recbot.scripts.rag import RAG
from django.views.decorators.csrf import csrf_exempt


rag = RAG()

@csrf_exempt
def recbotResponse(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    response = rag.output(body['conversation'], body['city'], body['neighborhood'])
    return JsonResponse(response)

def recbot(request):
    template = loader.get_template('starter.html')
    return HttpResponse(template.render())

@csrf_exempt
def recbotRecomender(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    list_dict_response = rag.get_list_similarity(body['embedding'], body['city'], body['neighborhood'])
    list_dict_response = [{"dish_id": str(l['_id']), "dish_name": l['name'], "restaurant_id": str(l['restaurant_id']), "score":l['score'], "sugestion":l['text']} for l in list_dict_response]
    return JsonResponse({'results': list_dict_response})
