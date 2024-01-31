import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from kafka import KafkaConsumer
import json
import logging

logging.basicConfig(level=logging.INFO)  # Imposta il livello di log a INFO o superiore
logger = logging.getLogger(__name__)


# Configurazione del consumatore
alert_bootstrap_servers = 'kafka:9092'
alert_group_id = 'gruppo-di-alert'
alert_auto_offset_reset = 'earliest'
regular_group_id= 'gruppo-di-regular'


# Creazione del consumatore
alert_consumer = KafkaConsumer(
    'AlertTopic',
    bootstrap_servers=alert_bootstrap_servers,
    group_id=alert_group_id,
    auto_offset_reset=alert_auto_offset_reset,
    consumer_timeout_ms=5000  # Tempo di attesa in millisecondi
)



# Configurazione del server SMTP
smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_username = 'myweatherdsb@gmail.com'
smtp_password = 'kidg ziwq dqgi ziqa'
sender_email = 'myweatherdsb@gmail.com'



# Funzione per inviare notifiche
# Funzione per inviare email
def send_email(subject, body, to_address):
    msg = MIMEMultipart()
    msg.attach(MIMEText(body, 'plain'))
    msg['Subject'] = subject
    msg['From'] = smtp_username
    msg['To'] = to_address

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_address, msg.as_string())



while True:
     for kafka_msg in alert_consumer:
        # Elaborare il messaggio ricevuto
        try:
            message_value_str = kafka_msg.value.decode('utf-8')
            logger.info('Messaggio ricevuto: %s', message_value_str)
            
            # Decodifica il messaggio JSON
            alert_message = json.loads(message_value_str)
            receiving_email = alert_message.get('email')
            logger.info('Email: %s', receiving_email)

            # Estrai i dati dall'alert
            alert_type = alert_message.get('type')
            alert_content = alert_message.get('message')

            # Esempio di invio email all'utente (da personalizzare)
            to_email = receiving_email  # Inserisci l'indirizzo email dell'utente
            email_subject = f'Weather Alert: {alert_type}'
            email_body = f'Dear User,\n\n{alert_content}\n\nBest regards,\nWeather Alert System'

            # Invio dell'email
            send_email(email_subject, email_body, to_email)
            logger.info("Email inviata")

        except json.JSONDecodeError as e:
            logger.error('Errore nel decodificare il messaggio JSON: %s', e)

