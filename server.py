from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}
animals_to_buy = ['слона', 'кролика']


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
    user_id = req['session']['user_id']

    if req['session']['new']:

        sessionStorage[user_id] = {
            'suggests': [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ]
        }
        res['response']['text'] = f'Привет! Купи {animals_to_buy[0]}!'
        res['response']['buttons'] = get_suggests(user_id)
        return

    if req['request']['original_utterance'].lower() in [
        'ладно',
        'куплю',
        'покупаю',
        'хорошо',
        'я покупаю',
        'я куплю'
    ]:
        res['response']['text'] = f'{animals_to_buy[0].capitalize()} можно найти на Яндекс.Маркете!'
        if len(animals_to_buy) > 1:
            del animals_to_buy[0]
            sessionStorage[user_id] = {
                'suggests': [
                    "Не хочу.",
                    "Не буду.",
                    "Отстань!",
                ]
            }
            res['response']['text'] += f"\nКупи {animals_to_buy[0]}!"
            res['response']['buttons'] = get_suggests(user_id)
        else:
            res['response']['end_session'] = True
            return

    else:
        res['response']['text'] = \
            f"Все говорят '{req['request']['original_utterance']}', а ты купи {animals_to_buy[0]}!"
        res['response']['buttons'] = get_suggests(user_id)


def get_suggests(user_id):
    session = sessionStorage[user_id]

    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in session['suggests'][:2]
    ]

    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    if len(suggests) < 2:
        suggests.append({
            "title": "Ладно",
            "url": f"https://market.yandex.ru/search?text={animals_to_buy[0][:-1]}",
            "hide": True
        })

    return suggests


if __name__ == '__main__':
    app.run()
