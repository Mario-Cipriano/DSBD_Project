from SLA_Manager import create_app

user_management = create_app() 

if __name__ == "__main__":
    user_management.run(host='0.0.0.0', port=3003, debug=True)