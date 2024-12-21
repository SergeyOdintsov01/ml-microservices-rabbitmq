import pika
import json
import pickle
import numpy as np


with open("myfile.pkl", "rb") as pkl_file:
    regressor = pickle.load(pkl_file)
    #print("Модель загрулилась!!!")

#-------СЕРВИС ДЛЯ ПРИЕМА ЗНАЧЕНИЙ ФИЧ, И ПОСЛЕДУЮЩЕ ОТПРАВКИ ПРЕДСКАЗАНИЯ(y_pred после отработки модели)-------
# Подключаемся с брокеру(RabbitMQ)
try:
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq", port=5672)
    )
    # Устанавливаем канал связи
    channel = connection.channel()
    # Задаем правила, т.е. какие очереди нас интересуют(как на прием сообщений, так и на отправку)
    # Сначала получим сообщение из очереди features для прогонки через regressor
    channel.queue_declare(queue="features")
    # Очередь для отправки сериализованно y_pred
    channel.queue_declare(queue="y_pred")

    class Messeges:
        def __init__(self):
            self.y_pred = None
            self.id = None

        def callback(self, ch, method, properties, body):
            try:
                features = json.loads(body)

                if 'body' in features and 'id' in features:
                    features_array = np.array(features['body']).reshape(1, -1)
                    self.y_pred = float(regressor.predict(features_array)[0])
                    self.id = features['id']
                    print(f"ПРЕДСКАЗАНИЕ: {self.y_pred}")
                    self.send_y_pred()
                else:
                    print("Ошибка: Неверный формат сообщения.")
            except Exception as e:
                print(f"Ошибка в callback: {e}")

        def send_y_pred(self):
            try:
                if self.id is not None and self.y_pred is not None:
                    message_model_result = {
                        'id': self.id,
                        'body': self.y_pred
                    }
                    channel.basic_publish(exchange="",
                                          routing_key="y_pred",
                                          body=json.dumps(message_model_result))
                    print("Предсказание y_pred отправлено в очередь")
                else:
                    print("Ошибка: Не удалось отправить сообщение. Предсказание или ID отсутствует.")
            except Exception as e:
                print(f"Ошибка при отправке сообщения: {e}")

    # Создадаю оюъект класса Messages
    message = Messeges()


    # Напишем basis_consume - получение сообщения подписчиком. 
    # Ведь наш сервис должен получить сообщение(вектор значений признаков)
    channel.basic_consume(queue="features", # из какой очереди ждем сообщения
                          on_message_callback=message.callback, # какую функцию вызвать при получении сообщения
                          auto_ack=True)
    #print("Ожидание сервисом сообщения из очереди features.Для принудительной остановки (CTRL+C)")


    # Запускаем режим ожидани сообщений нашего сервиса
    channel.start_consuming()
except Exception as e:
    print(f"Не удалось подключиться к очереди. Или другие проблемы: {e}")