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
    global game_on, cur_city
    user_id = req['session']['user_id']

    if req['session']['new']:
        cur_city = 0
        sessionStorage[user_id] = {
            'suggests': [
                "Давай",
                "Не хочу",
            ]
        }
        res['response']['text'] = 'Привет! Хочешь сыграть в игру "Угадай город"?'
        res['response']['buttons'] = get_suggests(user_id)
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

    if req['request']['original_utterance'].lower() == list(cities.keys())[cur_city] and game_on:
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
    ] and game_on:
        res['response']['text'] = 'Неверно! Угадывай дальше...'
        res['response']['buttons'] = get_suggests(user_id)
        return

    game_on = False
    res['response']['text'] = "Пока!"


def get_suggests(user_id):
    session = sessionStorage[user_id]

    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests']
    ]

    return suggests


if __name__ == '__main__':
    app.run()
