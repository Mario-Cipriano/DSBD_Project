from UserManager import create_app

user_management = create_app() #UserManagement app

if __name__ == "__main__":
    
    
    user_management.run(host='0.0.0.0', port=3001, debug=True)