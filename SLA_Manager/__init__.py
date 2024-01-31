from flask import Flask, request, jsonify,render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from prometheus_api_client import PrometheusConnect
import logging
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import NoResultFound



logging.basicConfig(level=logging.INFO)  # Imposta il livello di log a INFO o superiore
logger = logging.getLogger(__name__)

def create_app():
 
 app = Flask(__name__)
 app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+pymysql://root:toor@sla_managerDB:3306/sla_managerDB'
 app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 db = SQLAlchemy(app)
 prometheus_url = 'http://prometheus:9090'
 prometheus = PrometheusConnect(url=prometheus_url)

 class SLA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(255), nullable=False)
    min_value = db.Column(db.Float, nullable=False)
    max_value = db.Column(db.Float, nullable=False)
    is_selected = db.Column(db.Boolean, default=False)

 class VIOLATION(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sla_id = db.Column(db.Integer, db.ForeignKey('sla.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    actual_value = db.Column(db.Float, nullable=False)
    is_violated = db.Column(db.Boolean, nullable=False)

 def __str__(self):
      return f"message(id={self.id}, metric_name={self.metric_name}, min_value={self.min_value}, max_value={self.max}, is_selected={self.is_selected})"
 
 def convert_unix_datetime(unix_time):
    try:
        # Converti il timestamp UNIX in un oggetto datetime
        datetime_obj = datetime.utcfromtimestamp(int(unix_time))
        return datetime_obj
    except ValueError as e:
        print(f"Errore di conversione: {e}")
        return None
    
 @app.route('/sla', methods=['POST'])
 def create_sla():
    data = request.get_json()
    print(data)
    # Estrazione dei dati dal payload JSON
    for metrica in data:
        metric = metrica['metric']
        min_value = metrica['min_val']
        max_value = metrica['max_val']
        result = db.session.query(SLA).filter(SLA.metric_name==metric).first()
        if result is None:
            is_selected = True  # Poiché stai già iterando solo sui dati selezionati
            sla = SLA(metric_name=metric, min_value=min_value, max_value=max_value, is_selected=is_selected)
            db.session.add(sla)
        else:
            result.min_value = min_value
            result.max_value = max_value
            result.is_selected = True
    db.session.commit()
    return jsonify({"message": "tutto ok"})
 


 @app.route('/sla/status', methods=['GET'])
 def get_sla_status():
    try:
        metric_list=db.session.query(SLA).all()
        if not metric_list:
            return jsonify({"error": f"No SLA found"}), 404
        result_array = []
        with app.app_context():      
            # Ottieni tutte le righe SLA che corrispondono alla metrica specificata
             for metric in metric_list:
              logger.info("metric: %s",metric)
              query=f"{metric.metric_name}"
              metric_data=prometheus.custom_query(query=query)
              logger.info("metric_data: %s",str(metric_data))  

              for index in range(len(metric_data)):
               metric_value= float(metric_data[index]["value"][1])
               logger.info("metric_value: %s",str(metric_value))
               logger.info("timestamp: %s",str(convert_unix_datetime(metric_data[index]["value"][0])))

               if metric_value < float(metric.min_value) or metric_value > float(metric.max_value):
                  is_violated = True
               else: is_violated = False

               result = db.session.query(VIOLATION).filter(VIOLATION.sla_id==metric.id).first()
               logger.info("result1: %s",result)
               
               result_array.append({ 
                        "metric_name": metric.metric_name,
                        "actual_value": metric_value,
                        "min_value": metric.min_value,
                        "max_value": metric.max_value     
                    })
               if result is None:
                 violation=VIOLATION(sla_id=metric.id, timestamp=convert_unix_datetime(metric_data[index]["value"][0]), actual_value=metric_value, is_violated=is_violated)
                 db.session.add(violation)
               else:
                   result.timestamp = convert_unix_datetime(metric_data[index]["value"][0])
                   result.actual_value = metric_value
                   result.is_violated = is_violated    
               db.session.commit()
               break
            # Verifica violazione SLA per ogni SLA trovato
             return jsonify({"message": result_array})
    except NoResultFound:
        return jsonify({"error": f"No SLA found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error querying Prometheus: {str(e)}"}), 500

 @app.route('/sla/violations_for_hours', methods=['GET'])
 def get_sla_violation():
    try:
        metric_list=db.session.query(SLA).all()
        if not metric_list:
            return jsonify({"error": f"No SLA found"}), 404
        # Definisci il vettore di ore desiderate
        hours_vector = ["1h", "3h", "6h"]
        violations_array = []  # Array di mappe per salvare i valori di numbers_violations
        with app.app_context():      
            # Ottieni tutte le righe SLA che corrispondono alla metrica specificata
             for metric in metric_list:
              logger.info("metric: %s",metric)
              for hours in hours_vector:
               query=f"{metric.metric_name}[{hours}:20s]"
               logger.info("query: %s",query)
               metric_data=prometheus.custom_query(query=query)
               logger.info("metric_data: %s",str(metric_data))  
               query_violations_hours= f"sum(sum_over_time(count({metric.metric_name} < {metric.min_value} or {metric.metric_name} > {metric.max_value})[{hours}:20s]))"
               numbers_violations=prometheus.custom_query(query=query_violations_hours)
               logger.info("numero_violazioni: %s",numbers_violations)
               violations_array.append({ 
                        "metric_name": metric.metric_name,
                        "hours": hours,
                        "numbers_violations": numbers_violations[0]["value"][1]
                    })
             logger.info("violations_array: %s",violations_array)
              # Verifica violazione SLA per ogni SLA trovato
             return jsonify({"message": violations_array})
    except NoResultFound:
        return jsonify({"error": f"No SLA found"}), 404
    except Exception as e:
        return jsonify({"error": f"Error querying Prometheus: {str(e)}"}), 500


 @app.route('/sla/configure', methods=['GET'])
 def sla_configure():
   return render_template("configure_sla.html")

 return app





  
 

