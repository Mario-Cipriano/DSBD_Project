from MyWeatherHandler import create_app

weather_management = create_app() 

if __name__ == "__main__":
   
    
    weather_management.run(host='0.0.0.0', port=3002)