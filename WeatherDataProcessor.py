from kafka import KafkaConsumer, KafkaProducer
import json
import requests
import logging
import time

logging.basicConfig(level=logging.INFO)  # Imposta il livello di log a INFO o superiore
logger = logging.getLogger(__name__)

# Configurazione del consumatore
bootstrap_servers_consumer = 'kafka:9092'
group_id = 'gruppo-di-consumatori'
auto_offset_reset = 'earliest'
# Chiave api
api_key = '109a274e47fac26e28be9c3d15bbc8e6'

# Creazione del consumatore
consumer = KafkaConsumer(
    'PingRoute',
    bootstrap_servers=bootstrap_servers_consumer,
    group_id=group_id,
    auto_offset_reset=auto_offset_reset,
    consumer_timeout_ms=5000  # Tempo di attesa in millisecondi
)

bootstrap_servers_producer = 'kafka:9092'
producer = KafkaProducer(bootstrap_servers=bootstrap_servers_producer)
alert_topic = 'AlertTopic'


def get_weather_data(city, country):
    base_url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {'q': f'{city},{country}', 'appid': api_key, 'units': 'metric'}

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f'Errore nell\'ottenere i dati meteorologici per {city}, {country}. Codice di stato: {response.status_code}')
        return None


# try:
while True:
    for kafka_msg in consumer:
        # Elaborare il messaggio ricevuto
        try:
            logger.info("sono nel try")
            message_value_str = kafka_msg.value.decode('utf-8')
            logger.info('Messaggio ricevuto: %s', message_value_str)
            # Decodifica il messaggio JSON
            decoded_message = json.loads(message_value_str)

            # Estrai i dati dalla struttura del messaggio
            subscription_id = decoded_message.get('subscription_id')
            email = decoded_message.get('email')
            city = decoded_message.get('city')
            country_code = decoded_message.get('countrycode')
            minTemp = decoded_message.get('minTemp')
            maxTemp = decoded_message.get('maxTemp')
            rain = decoded_message.get('rain')
            snow = decoded_message.get('snow')

            # Fai qualcosa con i dati estratti
            logger.info('Subscription ID: %s', subscription_id)
            logger.info('Email: %s', email)
            logger.info('City: %s', city)
            logger.info('Country Code: %s', country_code)
            logger.info('Temp Min: %s', minTemp)
            logger.info('Temp Max: %s', maxTemp)
            logger.info('rain: %s', rain)
            logger.info('snow: %s', snow)

            # Ottieni dati meteorologici dalla API di OpenWeatherMap
            weather_data = get_weather_data(city, country_code)

            if weather_data:
                # Confronta i dati estratti con quelli dell'API
                api_min_temp = weather_data['main']['temp_min']
                api_max_temp = weather_data['main']['temp_max']
                api_rain = weather_data['rain']['1h'] if 'rain' in weather_data and '1h' in weather_data['rain'] else 0
                api_snow = weather_data['snow']['1h'] if 'snow' in weather_data and '1h' in weather_data['snow'] else 0

                # Stampa i dati estratti dall'API
                logger.info('Dati estratti dall\'API di OpenWeatherMap:')
                logger.info('Temperatura Minima: %s°C', api_min_temp)
                logger.info('Temperatura Massima: %s°C', api_max_temp)

                if 'rain' in weather_data and '1h' in weather_data['rain']:
                    logger.info('Pioggia nell\'ultima ora: %s mm', weather_data["rain"]["1h"])
                else:
                    logger.info('Pioggia nell\'ultima ora: 0 mm')

                if 'snow' in weather_data and '1h' in weather_data['snow']:
                    logger.info('Neve nell\'ultima ora: %s mm', weather_data["snow"]["1h"])
                else:
                    logger.info('Neve nell\'ultima ora: 0 mm')

                # Esegui confronti e stampa messaggi di avviso se necessario
                if minTemp != api_min_temp:
                    logger.warning('Avviso: Differenza nella temperatura minima. Messaggio: %s, API: %s', minTemp, api_min_temp)

                if maxTemp != api_max_temp:
                    logger.warning('Avviso: Differenza nella temperatura massima. Messaggio: %s, API: %s', maxTemp, api_max_temp)

                if rain != api_rain:
                    logger.warning('Avviso: Differenza nella pioggia. Messaggio: %s, API: %s', rain, api_rain)

                if snow != api_snow:
                    logger.warning('Avviso: Differenza nella neve. Messaggio: %s, API: %s', snow, api_snow)

                # Verifica Condizioni per l'alerts:
                if api_max_temp > maxTemp:
                    alert_message = {'type': 'MaxTempAlert', 'message': f'Avviso temperatura massima per {city}: {api_max_temp}°C', 'email': email}
                    producer.send(alert_topic, json.dumps(alert_message).encode('utf-8'))

                if api_min_temp < minTemp:
                    alert_message = {'type': 'MinTempAlert', 'message': f'Avviso temperatura minima per {city}: {api_min_temp}°C', 'email': email}
                    producer.send(alert_topic, json.dumps(alert_message).encode('utf-8'))

                if api_rain > rain:
                    alert_message = {'type': 'RainAlert', 'message': f'Avviso pioggia per {city}: {api_rain} mm', 'email': email}
                    producer.send(alert_topic, json.dumps(alert_message).encode('utf-8'))

                if 'snow' in weather_data and '1h' in weather_data['snow']:
                    alert_message = {'type': 'SnowAlert', 'message': f'Avviso neve per {city}: Nevicata di {weather_data["snow"]["1h"]} mm', 'email': email}
                    producer.send(alert_topic, json.dumps(alert_message).encode('utf-8'))

        except json.JSONDecodeError as e:
            logger.error('Errore nel decodificare il messaggio JSON: %s', e)
 


