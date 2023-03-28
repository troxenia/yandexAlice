from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}
cities = {'москва': ('213044/0c4a7b07600f86dabc90', '965417/a17817236707681e3e88'),
          'нью-йорк': ('1540737/7db993d2bd159085dc7f', '937455/a2e0a1798fccfd264078'),
          'париж': ('1656841/0a47f31f1792024ecad5', '1533899/fbe5c6c3611289f7dcf5')}
cur_city = 0
game_on = False
name = None


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')

    return jsonify(response)


def handle_dialog(req, res):
    global game_on, cur_city, name
    user_id = req['session']['user_id']

    if req['session']['new']:
        cur_city, name = 0, None
        res['response']['text'] = 'Привет, назови свое имя.'
        res['response']['buttons'] = get_suggests(user_id)
        return

    if any(line in req['request']['nlu']['tokens'] for line in ['помощь', 'помоги']):
        res['response']['text'] = 'Справка по игре:\nНазови свое имя и начни игру. ' \
                                  'Тебе нужно угадать город, картинку которого я покажу. Ты можешь ' \
                                  'попытаться ответить, попросить подсказку или сдаться, а также окончить игру.\n' \
                                  'Когда у меня закончатся картинки, игра тоже будет окончена.\n' \
                                  'Надеюсь, теперь ты можешь ответить на предыдущий вопрос.'
        res['response']['buttons'] = get_suggests(user_id)
        return

    if name is None:
        if get_first_name(req) is not None:
            name = get_first_name(req).capitalize()
            sessionStorage[user_id] = {
                'suggests': [
                    "Давай",
                    "Не хочу",
                ]
            }
            res['response']['text'] = f'Приятно познакомиться, {name}! Хочешь сыграть в игру "Угадай город"?'
            res['response']['buttons'] = get_suggests(user_id)
            return

        res['response']['text'] = f'Пожалуйста, назови свое имя.'
        return

    if req['request']['original_utterance'].lower() in [
        'давай',
        'сыграем',
        'играю',
        'сыграю',
        'да',
        'дальше',
        'играем',
        'хочу',
        'я хочу',
        'я сыграю'
    ]:
        game_on = True
        sessionStorage[user_id] = {
            'suggests': [
                "Картинка-подсказка",
                "Сдаюсь",
            ]
        }
        res['response']['text'] = 'text'
        res['response']['card'] = {
            "type": "BigImage",
            "image_id": cities[list(cities.keys())[cur_city]][0],
            "title": "Угадай город на картинке"
        }
        res['response']['buttons'] = get_suggests(user_id)
        return

    if game_on:
        if get_city(req) == list(cities.keys())[cur_city]:
            cur_city += 1
            game_on = False
            if cur_city < len(cities):
                sessionStorage[user_id] = {
                    'suggests': [
                        "Дальше",
                        "Не хочу",
                    ]
                }
                res['response']['text'] = 'Правильно, молодец! Играем дальше?'
                res['response']['buttons'] = get_suggests(user_id)
            else:
                res['response']['text'] = 'Правильно, молодец! Игра окончена.'
            return

        if req['request']['original_utterance'].lower() in [
            'картинка-подсказка',
            'подсказка',
            'подскажи'
        ]:
            sessionStorage[user_id] = {
                'suggests': [
                    "Сдаюсь"
                ]
            }
            res['response']['text'] = 'text'
            res['response']['card'] = {
                "type": "BigImage",
                "image_id": cities[list(cities.keys())[cur_city]][1],
                "title": "Угадай город на картинке"
            }
            res['response']['buttons'] = get_suggests(user_id)
            return

        if req['request']['original_utterance'].lower() in [
            'сдаюсь',
            'я сдаюсь'
        ]:
            cur_city += 1
            game_on = False
            if cur_city < len(cities):
                sessionStorage[user_id] = {
                    'suggests': [
                        "Дальше",
                        "Не хочу",
                    ]
                }
                res['response']['text'] = f'Правильный ответ - {list(cities.keys())[cur_city - 1].capitalize()}! ' \
                                          f'Играем дальше?'
                res['response']['buttons'] = get_suggests(user_id)
            else:
                res['response']['text'] = f'Правильный ответ - {list(cities.keys())[cur_city - 1].capitalize()}! ' \
                                          f'Игра окончена.'
            return

        if not req['request']['original_utterance'].lower() in [
            'заканчиваем',
            'не хочу',
            'не буду',
            'нет',
            'не надо',
            'заканчивай',
            'не играю',
            'не играем'
        ]:
            if get_city(req) is None:
                res['response']['text'] = 'Это даже не город! Угадывай дальше...'
            else:
                res['response']['text'] = 'Неверно! Угадывай дальше...'
            res['response']['buttons'] = get_suggests(user_id)
            return

    game_on = False
    res['response']['text'] = "Пока!"


def get_suggests(user_id):
    suggests = [{'title': 'Помощь', 'hide': True}]
    if user_id in sessionStorage:
        session = sessionStorage[user_id]

        suggests += [
            {'title': suggest, 'hide': True}
            for suggest in session['suggests']
        ]

    return suggests


def get_city(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.GEO':
            return entity['value'].get('city', None)


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)


if __name__ == '__main__':
    app.run()
