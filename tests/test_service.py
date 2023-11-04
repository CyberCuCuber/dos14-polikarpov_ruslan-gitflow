import requests
import json

HOST = "https://ivanoff.smodata.net/authn/"
LOGIN = f"{HOST}api/v1/identity/login"
VALIDATE = f"{HOST}api/v1/identity/validate"
IDENTITY = f"{HOST}api/v1/identity"
HEALTH = f"{HOST}api/v1/authn/health_check"

def get_login(valid_flag="valid"):
	valid_login = "optimistic_bohr"
	valid_pass = "cLckl2OBM9cfi886epu6EEk9ygHxUsQD"
	failed_login = "optimistic_boh"
	failed_pass = "2OBM9cfi886epu6EEk9ygHxUsQD"
	match valid_flag:
		case "valid":
			return {"login": valid_login, "password": valid_pass}
		case "password": 
			return {"login": valid_login, "password": failed_pass}
		case "login":
			return {"login": failed_login, "password": valid_pass}
		case "all":
			return {"login": failed_login, "password": failed_pass}
		case "key":
			return {"password": failed_pass}

def get_token(valid_flag=True):
	valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiIxIn0.r4RVPHpZE0aWNQxjlGEetMHTltB-EJzORuK3zWdTp_I"
	failed_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiIxIn0.Xe7n_cOWmMZJ8j08c2C_M_5A3DCobSiO5P18DMQf0Vo"
	if valid_flag:
		return {"token": valid_token}
	else:
		return {"token": failed_token}
	
def get_identity(valid_flag="valid"):
	valid_id = 18
	valid_login = "kurelikaaa"
	valid_pass = "123qweasdQWSEASD"
	failed_id = "122"
	failed_login = "optimistic_bohr"
	failed_pass = "123asd"

	match valid_flag:
		case "valid":
			return {"client_id": valid_id, "login": valid_login, "password": valid_pass}
		case "id":
			return {"client_id": failed_id, "login": valid_login, "password": valid_pass}
		case "login":
			return {"client_id": valid_id, "login": failed_login, "password": valid_pass}
		case "password":
			return {"client_id": valid_id, "login": valid_login, "password": failed_pass}
		case "key":
			return {"login": valid_login, "password": failed_pass}

def request(method: str, data: dict, url="http://localhost"):
	response = ""
	match method:
		case "get":
			response = requests.get(url, json=data)
		case "post":
			response = requests.post(url, json=data)
		case "put":
			response = requests.put(url, json=data)
	return [response.status_code, response.text]


def check_links():
	print("---Check links---")
	print("---Checking health---")
	print(request("get", {}, HEALTH))
	print("---Checking login---")
	print(request("post", get_login(), LOGIN))
	print("---Checking validate---")
	print(request("get", get_token(), VALIDATE))
	print("---Checking identity---")
	print(request("put", get_identity(), IDENTITY))
	
if __name__ == "__main__":
	check_links()
