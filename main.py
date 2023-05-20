from datetime import datetime, timedelta
from flask import Flask, request, make_response, abort
import hashlib
import yaml
import jwt
import base64

SECRET = b'MXEydzNlNHI1dFQlUiRFI1dAUSE='


class Error(Exception):
    """Base user exception class"""
    pass


class WeakPassword(Error):
    """Wrong password exception"""
    pass


class InaccessibleID(Error):
    """Inaccessible ID exception"""
    pass


class WrongToken(Error):
    """Wrong token exception"""
    pass


class StringValidation:
    """
    Validation string
    """

    def __init__(self, string):
        """
        Validation string
        :param string: string
        """
        self.string = string

    def check_length(self):
        """
        Checks length string
        :return: True or False
        """
        if len(self.string) >= 8:
            return True
        else:
            return False

    def check_numbers(self):
        """
        Checks number in string
        :return: True or False
        """
        if any(ch.isdigit() for ch in self.string) and not self.string.isdigit():
            return True
        else:
            return False

    def check_upper_lower(self):
        """
        Checks upper and lower letters in string
        :return: True or False
        """
        if self.string.isupper() or self.string.islower():
            return False
        else:
            return True


class Password(StringValidation):
    """
    Child class from StringValidation
    """

    def __init__(self, password):
        """
        Validate user password
        :param password: password string
        """
        super().__init__(password)
        if self.check_length() and self.check_numbers() and self.check_upper_lower():
            self.__password = hashlib.sha512(password.encode()).hexdigest()
        else:
            self.__password = None

    @property
    def passwd(self):
        return self.__password


class Users:
    """
    Users class
    """

    def __init__(self, users_yaml: str):
        """
        Creates all registered users
        :param users_yaml: yaml file with users
        """
        self.__users = {}
        self.__users_id_login = {}
        self.users_yaml = users_yaml
        self.read_yaml()

    def read_yaml(self):
        """
        Reads yaml file and adds users obj
        :return: None
        """
        with open(self.users_yaml, "r") as file:
            yml = yaml.load(file, Loader=yaml.FullLoader)
            for types in yml:
                for user in yml[types]:
                    if self.validate_passwd(user["password"]) is not None:
                        passwd = Password(user["password"]).passwd
                        self.add_user(user["login"], passwd, user["client_id"])

    @staticmethod
    def validate_passwd(password):
        """
        Static valid password in sha512
        :param password: password
        :return: Valid password in sha512
        """
        return Password(password).passwd

    def add_user(self, login, passwd, client_id):
        """
        Adds user obj to users dict
        :param login: login
        :param passwd: valid password in sha512
        :param client_id: user id
        :return: None
        """
        self.__users[login] = User(login, passwd, client_id)
        user_data = [{
            "id": client_id,
            "login": login,
            "password": passwd
        }]
        with open("logins_sha.yaml", "a") as yaml_file:
            yaml.dump(user_data, yaml_file)
        self.__users_id_login[client_id] = login

    @property
    def get_users(self):
        return self.__users

    def check_id(self, client_id):
        """
        Checks availability of ID
        :param client_id: id
        :return: True if ID is available
        """
        if client_id in self.__users_id_login:
            return True
        else:
            return False

    def login_att_response(self, input_login, input_password):
        """
        Attemption to log in with response
        :param input_login: user login
        :param input_password: user password
        :return: JWT with client id payload - success, False - wrong password, None - unknown login
        """
        try:
            response = self.get_users[input_login].login_attempt(input_password)
            return response
        except KeyError:
            return None

    def check_jwt(self, token):
        """
        Validate JWT token
        :param token: JWT-token
        :return: exception - wrong token, client id - success
        """
        token_id = jwt.decode(token, base64.b64decode(SECRET).decode(), algorithms=["HS256"])["client_id"]
        if self.check_id(token_id):
            return token_id
        else:
            raise WrongToken

    def register_user(self, reg_id, reg_login, reg_password):
        """
        Validate and register new user
        :param reg_id: id to register
        :param reg_login: login to register
        :param reg_password: password to register
        :return: None
        """
        hash_password = self.validate_passwd(reg_password)
        if not self.check_id(reg_id) and reg_login not in self.get_users.keys():
            if hash_password is not None:
                self.add_user(reg_login, hash_password, reg_id)
            else:
                raise WeakPassword
        else:
            raise InaccessibleID


class User:
    """
    Class User
    """

    def __init__(self, login, password, user_id):
        """
        User obj
        :param login: user login
        :param password: password in sha512 encoding
        :param user_id: user id
        """
        self.__login = login
        self.__password = password
        self.__id = user_id
        self.__blocked = False
        self.__block_time = None
        self.__failure_cont = 0

    @property
    def login(self):
        return self.__login

    @property
    def passwd(self):
        return self.__password

    @property
    def user_id(self):
        return self.__id

    @property
    def block(self):
        return self.__blocked

    @property
    def failure(self):
        return self.__failure_cont

    @block.setter
    def block(self, inf=True):
        """
        Add or delete blocking to User
        :param inf: add or del blocking, str
        :return:
        """
        self.__blocked = inf
        self.__block_time = datetime.now() + timedelta(minutes=2)

    @block.deleter
    def block(self):
        self.__blocked = False
        self.__block_time = None
        del self.failure

    @failure.deleter
    def failure(self):
        """
        Reset failure count
        :return: None
        """
        self.__failure_cont = 0

    @failure.setter
    def failure(self, inf=False):
        match inf:
            case True:
                self.__failure_cont += 1

    def check_fails(self):
        """
        Checks failure count and block user if too many fails make
        :return: None
        """
        if self.failure >= 3:
            self.block = True

    def check_block(self):
        """
        Checks if the user is locked out and unlocks if the lock timeout expires
        :return: True if the user is locked out, False if the user is still locked out
        """
        if datetime.now() >= self.__block_time:
            del self.block

    def make_jwt(self):
        """
        Makes JWT with client id payload
        :return: JWT
        """
        return jwt.encode({"client_id": self.user_id}, base64.b64decode(SECRET).decode(), algorithm="HS256")

    def login_attempt(self, input_password):
        """
        Attempt to log in
        :param input_password: password to validate
        :return: False - wrong password, JWT - success
        """
        if self.block:
            self.check_block()
        if input_password != self.passwd or self.block:
            self.failure = True
            self.check_fails()
            return False
        else:
            return self.make_jwt()


#Очищаем файл с паролями login_sha.yaml
with open("logins_sha.yaml", "w") as fil:
    fil.write("")

#Создаём объект со всеми пользователями
users = Users("logins.yaml")

#Создаём объект приложения Flask
app = Flask(__name__)


@app.route("/api/v1/identity/login", methods=["POST"])
def app_login():
    """
    Обработка POST-метода для попытки входа
    :return: отправляет ответ с токеном JWT
    """
    request_data = request.json
    login = request_data["login"]
    password = hashlib.sha512(request_data["password"].encode()).hexdigest()
    resp = users.login_att_response(login, password)
    print(resp)
    if resp:
        response = make_response({"token": resp})
        response.status = 200
    else:
        response = make_response({
            "status": "error",
            "message": "login or password incorrect"
        })
        response.status = 403
    return response


@app.route("/api/v1/identity/validate", methods=["GET"])
def app_token_validate():
    """
    Обрабатывает GET-запрос валидации токена
    :return: Отправляет ответ с ID юзера
    """
    request_data = request.json
    token = request_data["token"]
    try:
        resp = users.check_jwt(token)
        response = make_response({"client_id": resp})
        response.status = 200
        return response
    except:
        abort(403)


@app.route("/api/v1/identity", methods=["PUT"])
def app_register_user():
    """
    Обработка PUT-запроса создания нового пользователя
    :return:
    """
    request_data = request.get_json()
    try:
        users.register_user(
            request_data["client_id"],
            request_data["login"],
            request_data["password"]
        )
        message = {"status": "ok"}
        response = make_response(message)
        response.status = 200
    except WeakPassword:
        message = "<Something wrong>"
        response = make_response({"status": "error", "message": message})
        response.status = 403
    except InaccessibleID:
        message = f"Login and password for client {request_data['client_id']} already exists"
        response = make_response({"status": "error", "message": message})
        response.status = 403
    return response


app.run()
