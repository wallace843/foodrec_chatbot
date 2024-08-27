import json
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from recbot.src.model.chat_output import ChatOutput

out = ChatOutput()

@csrf_exempt
def recbotResponse(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    response = out.bot_response(body['conversation'], body['city'], body['neighborhood'])
    return JsonResponse(response)

def recbot(request):
    template = loader.get_template('starter.html')
    return HttpResponse(template.render())

@csrf_exempt
def recbotRecomender(request):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    list_dict_response = out.recomender_response(body['embedding'], body['city'], body['neighborhood'])
    list_dict_response = [{"dish_id": str(l['_id']), "dish_name": l['name'], "restaurant_id": str(l['restaurant_id']), "score":l['score'], "sugestion":l['text']} for l in list_dict_response]
    return JsonResponse({'results': list_dict_response})
