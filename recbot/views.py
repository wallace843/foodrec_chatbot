import json
from django.template import loader
from django.http import HttpResponse, JsonResponse
from recbot.scripts.rag import RAG
from django.views.decorators.csrf import csrf_exempt


rag = RAG()

def recbotResponse(request):
    text = request.GET.get('text')
    response = rag.output(text)
    restaurants = [{"_id":r[0].metadata["_id_restaurant"],"id_dish":str(r[0].metadata["_id"]),"score":r[1]} for r in response["list_dish_documents"]]
    dict_response = {"response" : response["response"], "restaurants":restaurants}
    return JsonResponse(dict_response)

def recbot(request):
    template = loader.get_template('starter.html')
    return HttpResponse(template.render() )

@csrf_exempt
def recbotRecomender(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    list_dict_response = rag.get_list_similarity(body['embedding'], body['city'], body['neighborhood'])
    list_dict_response = [{"dish_id": str(l['_id']), "restaurant_id": str(l['restaurant_id']), "score":l['score']} for l in list_dict_response]
    return JsonResponse({'results': list_dict_response})
