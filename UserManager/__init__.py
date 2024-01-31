from flask import Flask, render_template,jsonify,request,redirect,url_for
from config import Config
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import re
import hashlib
from multiprocessing import Value




def create_app(config = Config):

   #Creazione del modulo flask
   app = Flask(__name__)
  
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:toor@utenteDB:3306/utenteDB'#os.environ.get('DATABASE_URI')
   app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
   #secret_key = secrets.token_hex(16) 
   #print(secret_key)
   app.config['SECRET_KEY'] = 'okk'#secret_key
   app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1) # Imposta la durata della sessione a 1 ora (in secondi)
   app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=1)
   

   #Dopo aver recuperato dal file config le configurazioni del database, si ottiene l'istanza
   #del database SQL 

   db = SQLAlchemy(app)
   login_manager = LoginManager(app)
   login_manager.login_view = 'login'
   #login_manager.remember_cookie_duration = timedelta(seconds=20)
   

   #Si definiscono quindi i modelli delle tabelle che compongo il db
   class USERS(UserMixin,db.Model):
     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
     nome = db.Column(db.String(100), nullable=False, unique = False)
     cognome = db.Column(db.String(100), nullable=False, unique = False)
     email = db.Column(db.String(100), nullable=False, unique=True)
     password = db.Column(db.String(100), nullable=False, unique=False)
   

   def __init__(self,nome,cognome,email, password):
        self.nome = nome
        self.cognome= cognome
        self.email = email
        self.password = password
      
   def get_id(self):
      return str(self.id)
   
   @login_manager.user_loader
   def load_user(user_id):
      return USERS.query.get(int(user_id))
   

   @app.route("/login", methods=['POST', 'GET'])
   def login():
      if(request.method == 'GET'):  
       #  print(os.environ.get('DATABASE_URI'))
         return render_template("login.html")
      else:
         message= None
         data= request.form
         hashed_password = hashlib.sha256(data['password'].encode('utf-8')).hexdigest()
         user = USERS.query.filter_by(email=data['email'])
         if user.first()!=None:  
            if user.first().password==hashed_password:
              login_user(user.first(),remember=True)
              var = "Login avvenuto con successo!"
              return render_template("login.html", var=var) 
            else:
              message ="Login fallito. Password errata"
              return render_template("login.html", error = message) 
         else:
            #error message. User not found
            message = "Login fallito. Email non trovata."
            return render_template("login.html", error = message)
   
   
   @app.route("/register", methods=['POST', 'GET'])
   def register():
      new_user= None
      email_pattern = r"^\S+@\S+\.\S+$"
      message= None
      var = None

      if(request.method == 'GET'):  
         return render_template("register.html")
      else:
            data = request.form
            if data['nome'].isspace() == True or len(data['nome']) < 3:
             message="Nome non valido. Inserisci almeno tre caratteri"
             return render_template("register.html",error=message)
            if data['cognome'].isspace() == True or len(data['cognome']) < 3:
             message ="Cognome non valido. Inserisci almeno tre caratteri"
             return render_template("register.html",error=message)
            if re.match(pattern=email_pattern, string=data['email']) == None: 
             message ="L'indirizzo email non è valido. Riprova"
             return render_template("register.html", error = message)
            else:
             new_user= db.session.query(USERS).filter(USERS.email == data['email'])
             if new_user.first() != None: 
               message ="L'email è gia in uso"
               return render_template("register.html", error = message)
             else:
               pass
            if len(data['password']) <5:
             message ="La password è troppo corta. Inserisci almeno 5 caratteri"
             return render_template("register.html", error = message)
            if data['password'] != data['confermapassword']:
                message= "La password non coincide"
                return render_template("register.html", error = message)
            if 'nome' in data and 'cognome' in data and 'email' in data and 'password' in data:
             hashed_password = hashlib.sha256(data['password'].encode('utf-8')).hexdigest()
             new_user = USERS(
                nome=data['nome'],
                cognome=data['cognome'],
                email=data['email'],
                password=hashed_password
            )
            if new_user is not None:
                db.session.add(new_user)
                db.session.commit()
                var = "Registrazione avvenuta con successo!"
                login_user(new_user,remember=True)
                return render_template("register.html", var =var)             
            else: 
               message = "Errore durante la creazione dell'utente. Riprova."               
               return render_template("register.html", error=message)
        
        
   @app.route("/home")
   @login_required
   def home():
      return render_template("home.html", utente=current_user)
   
   @app.route("/check_session")
   def check_session():
    if current_user.is_authenticated:
        return render_template("home.html")
    else:
     return redirect(url_for('login'))
   
   @app.route("/logout")
   @login_required
   def logout():
      logout_user() 
      return redirect(url_for('login'))

   @app.route("/MySubscriptions")    
   def MySubscriptions():
       return render_template("MySubscriptions.html") 

   return app    

