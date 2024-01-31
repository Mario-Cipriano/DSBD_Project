

import os

class Config:
   SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', default='mysql+pymysql://root:toor@utenteDB:3306/utenteDB')
   SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', default='mysql+pymysql://root:toor@weatherDB:3306/weatherDB')
   SQLALCHEMY_TRACK_MODIFICATIONS  =False
 


