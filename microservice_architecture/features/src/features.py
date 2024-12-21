import pika, json
import numpy as np
#import pandas as pd
from sklearn.datasets import load_diabetes
import time
from datetime import datetime

while True:
    try:
        #time.sleep(3)
        # np.random.seed(42)
        # Загружаем датасет о диабете. И заодно посмотрим размерность, чтобы совпадали размерность тренировочных и тестовых
        # для дальнейшей корректной работы
        X, y = load_diabetes(return_X_y=True)       

        # print(X.shape) # (442, 10)
        # print(y.shape) # (442,)
        # print(type(X))  # <class 'numpy.ndarray'>
        # print(X[:5])    # Посмотреть первые 5 элементов массива       

        # df = pd.DataFrame(X)  # pd.DataFrame(X, columns=["feature_" + str(i) in range(X.shape[1])]) - если захотим датафрейм с названиями столбцов
        # print(df.head(5))
        # print("="*100)
        # print(df.tail(5))     

        # Формируем случайный индекс строки.
        # Таким образом мы сможем получить случайный вектор признаков X[random_rom]
        # и истинный ответ для него y[random_row]
        # randint(low, high) -> с low до high; low == 0, high == количество строк массива с данными - 1
        # В примере ошибка, -1 - лишняя. Так как генерится номер строки в массиве с индексами 0-441, 
        # а функция np.random.randint(нижняя граница(включительно), верхняя(НЕ включительно)).
        # В дальнейшем можно без -1
        random_row = np.random.randint(0, X.shape[0]-1)     
        
        #Создаем метку сообщения. Она должна быть одинакова для истинных значений и для списка значений фич.
        message_id = datetime.timestamp(datetime.now())

        #-------СЕРВИС ОТПРАВКИ ЗНАЧЕНИЙ features И ИСТИННОГО y_true-------
        # Подключаемся к брокеру сообщений(RabbitMQ), для возмождности отправки сообщений от Producer(издатель) и Брокером:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq", port=5672)
        )   
        # Создаётся канал — основное средство взаимодействия с брокером(RabbitMQ). 
        # Все операции (например, публикация и получение сообщений) будут выполняться через каналы.
        channel = connection.channel()      

        # Создаём очередь y_true
        channel.queue_declare(queue='y_true')     

        # Создаем сообщения, для передачи в очередь y_true
        message_y_true = {
            'id' : message_id,
            'body': y[random_row]
        }  

        # Сообщение отправляется брокеру от издателя:
        # Как мы знаем, в RabbitMQ сообщения не отправляются сразу в очередь, 
        # а проходят через точку обмена (exchange). 
        # Сейчас нам достаточно знать, что точку обмена по умолчанию можно определить, указав пустую строку.
        channel.basic_publish(exchange="",
                              routing_key="y_true",
                              body=json.dumps(message_y_true))
        print("Сообщение с правильным ответом отправлено в очередь y_true")     

        # Создадим очередь для данных строкИ-значений фич  датасета.
        channel.queue_declare(queue="features")

        # Создаем сообщения, для передачи в очередь features
        message_features = {
            'id' : message_id,
            'body': list(X[random_row])
        }

        # Публикуем сообщение 
        channel.basic_publish(exchange='',
                              routing_key='features',
                              # Сереализируем объект(сообщение). json.dumps метод возвращает строку в формате JSON
                              # не получится сериализовать объект array — поэтому list()
                              body=json.dumps(message_features))
        #print("Сообщение в виде вектора со значениями наших фичей отправлено в очередь features")       

        # Закрываем соединение
        connection.close()
        time.sleep(5)
    except:
        print("Не удалось подключиться к очереди")