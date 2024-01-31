from flask import Flask, render_template,jsonify,request,redirect
from config import Config
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import kafka
import threading
import json
import time
from multiprocessing import Value


class message:
   def __init__(self, subscription_id,email,city,countrycode,minTemp,maxTemp,rain,snow):       
      self.subscription_id = subscription_id
      self.email=email
      self.city = city
      self.countrycode = countrycode
      self.minTemp = minTemp
      self.maxTemp = maxTemp
      self.rain = rain
      self.snow = snow

   
   
   def to_json(self):
        return {
            'subscription_id': self.subscription_id,
            'email':self.email,
            'city': self.city,
            'countrycode': self.countrycode,
            'minTemp': self.minTemp,
            'maxTemp': self.maxTemp,
            'rain': self.rain,
            'snow': self.snow
        }
      
   def __str__(self):
      return f"message(subscription_id={self.subscription_id}, email={self.email}, city={self.city}, countrycode={self.countrycode}, minTemp={self.minTemp}, maxTemp={self.maxTemp}, rain={self.rain}, snow={self.snow})"
   def __repr__(self):
      return self.__str__()
   
mutex_db = threading.Lock()
#Logger
#logger = logging.Logger(level=logging.DEBUG, name="Vattela a pesca")
logging.basicConfig(level=logging.DEBUG)

def create_app(config = Config):
   producer = kafka.KafkaProducer(bootstrap_servers = ["kafka:9092"])

   #Creazione del modulo flask
   app = Flask(__name__)

   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:toor@weatherDB:3306/weatherDB'
   app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
   #secret_key = secrets.token_hex(16) 
   #print(secret_key)
   app.config['SECRET_KEY'] = 'okk'#secret_key
   
   #Dopo aver recuperato dal file config le configurazioni del database, si ottiene l'istanza
   #del database SQL 
  
   db = SQLAlchemy(app)

   #Si definiscono quindi i modelli delle tabelle che compongo il db
   class SUBSCRIPTIONS(db.Model):
     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
     email = db.Column(db.String(100), nullable=False)
     city= db.Column(db.String(100), nullable=False)
     countrycode=db.Column(db.String(10), nullable=False)
     minTemp=db.Column(db.Float, nullable=False)
     maxTemp=db.Column(db.Float, nullable=False)
     rain=db.Column(db.Float, nullable=False)
     snow=db.Column(db.Boolean, nullable=False)
   

   def __init__(self,email,city,countrycode,minTemp,maxTemp,rain,snow):
        self.email = email
        self.city = city
        self.countrycode = countrycode
        self.minTemp = minTemp
        self.maxTemp = maxTemp
        self.rain = rain
        self.snow = snow

   def __str__(self):
      return(
         f"email: {self.email}. city: {self.city}. countrycode: {self.countrycode}. minTemp: {self.minTemp}. maxTemp: {self.maxTemp}. rain: {self.rain}. snow: {self.snow}. "
      )
   
   def __repr__(self):
      return self.__str__()
   

   class QueryMetrics:
    query_duration = Value('d', 0.0)
    
   @app.route("/metrics",methods=['GET'])
   def metrics():
      #with query_duration.get_lock():
      data = {
            "query_duration": str(QueryMetrics.query_duration.value)  
        }
      return json.dumps(data)

   #scheduler = BackgroundScheduler()
   def queryDB(db,app):
      app.logger.debug("Il thread sta eseguendo. By logger")
      with app.app_context(), mutex_db:
         start_time=time.time()
         subscriptions = db.session.query(SUBSCRIPTIONS).all()
         end_time=time.time()
         QueryMetrics.query_duration.value= end_time-start_time
         for subscription in subscriptions:
            msg = message(subscription.id, subscription.email, subscription.city, subscription.countrycode, subscription.minTemp, subscription.maxTemp, subscription.rain, subscription.snow)
            logging.debug(subscriptions)
            #code to send the kafka message...
            producer.send("PingRoute", json.dumps(msg.to_json()).encode('utf-8'))#bytes(str(msg),'utf-8'))

   scheduler = BackgroundScheduler()
   scheduler.add_job(queryDB, 'interval', seconds= 60, args=[db, app])   
   scheduler.start()          
   
   @app.route("/sendRequest", methods=['POST'])
   def sendRequest():
      if(request.method != 'POST'):  
       #  print(os.environ.get('DATABASE_URI'))
         return render_template("login.html")
      else:
         new_request= None
         data= request.form
      
         email= data["current_user_email"]
         city = data['city']
         countrycode = data['countrycode']
         minTemp = float(data['minTemp'])
         maxTemp = float(data['maxTemp'])
         rain = float(data['rain'])
         snow = data['snow']== 'yes'
         
         new_request = SUBSCRIPTIONS(
               email=email,
               city=city,
               countrycode=countrycode,
               minTemp=minTemp,
               maxTemp=maxTemp,
               rain=rain,
               snow=snow
            )
         if new_request is not None:
                db.session.add(new_request)
                db.session.commit()
                return redirect("/home")
         else:
                pass
      
   @app.route("/get_subscriptions/<email>", methods=['GET'])
   def get_preferiti(email):
    subscriptions_data = SUBSCRIPTIONS.query.filter(SUBSCRIPTIONS.email == email).all()

    if subscriptions_data:
        subscriptions = []
        for subscription in subscriptions_data:
            subscription_dict = {
                "id": subscription.id,
                "city": subscription.city,
                "countrycode": subscription.countrycode,
                "minTemp": subscription.minTemp,
                "maxTemp": subscription.maxTemp,
                "rain": subscription.rain,
                "snow": subscription.snow
            }
            subscriptions.append(subscription_dict)

        return jsonify(subscriptions)
    else:
        return jsonify({"error": "Nessun preferito trovato per l'utente con email {}".format(email)}), 404
   
   
   @app.route("/delete/<id>", methods=['GET', 'POST'])
   def delete(id):
    subscription = SUBSCRIPTIONS.query.get(id)

    if subscription:
        # Elimina la sottoscrizione dal database
        db.session.delete(subscription)
        db.session.commit()

    # Esempio di redirezione a una pagina dopo l'eliminazione
    return redirect("/MySubscriptions")
   
   return app    




