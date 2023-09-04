from datetime import datetime, timedelta
from flask import Flask, request, make_response
from os import environ
from sqlalchemy import create_engine, Column, String, Integer, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base

import hashlib
import yaml
import jwt
import base64


ENGINE = create_engine(f"postgresql://{environ.get('DB_USER')}:{environ.get('DB_PASS')}@{environ.get('DB_LOC')}:{environ.get('DB_PORT')}/{environ.get('DB_NAME')}")

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


class Broken_session_DB(Error):
    """Failed session exeption"""
    pass


Base = declarative_base()

class UserDB(Base):
    __tablename__ = "authn"

    client_id = Column(Integer, primary_key=True, nullable=False)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    block = Column(Boolean, unique=False)

    def __repr__(self):
        return f"<User {self.client_id} - {self.login}>"
    
    @classmethod
    def create_session(cls):
        Session = sessionmaker(bind=ENGINE)
        return Session()

    @classmethod
    def add_user(cls, client_id, login, password):
        user = cls(client_id=client_id, login=login, password=password, block=False)
        session = cls.create_session()
        session.add(user)
        #try to commit new user
        try:
            session.commit()
        except IntegrityError as ie:
            session.rollback()
            raise Broken_session_DB
        finally:
            session.close()
    
    @classmethod
    def get_all_users(cls):
        session = cls.create_session()
        users = session.query(UserDB).all()
        users_dict = {}
        for us in users:
            us_dict = {
                "login": str(us.login),
                "password": str(us.password),
                "block": str(us.block)
            }
            users_dict[f"{us.client_id}"] = us_dict
        session.close()
        return users_dict
    
    @classmethod
    def get_user_by_login(cls, login):
        session = cls.create_session()
        user = session.query(UserDB).filter(UserDB.login == login).first()
        user_dict = {
            "client_id": user.client_id,
            "login": user.login,
            "password": user.password,
            "block": user.block
        }
        session.close()
        return user_dict
    
    @classmethod
    def blocking(cls, login, block_flag=True):
        session = cls.create_session()
        user = session.query(UserDB).filter(UserDB.login == login).first()
        user.block = block_flag
        try:
            session.commit()
            return True
        except IntegrityError as ie:
            session.rollback()
            return False
        finally:
            session.close()

Base.metadata.create_all(ENGINE)


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

    def __init__(self, password=None, sha=False):
        """
        Validate user password
        :param password: password string
        """
        super().__init__(password)
        if password is not None and self.check_length() and self.check_numbers() and self.check_upper_lower() and not sha:
            self.__password = hashlib.sha512(password.encode()).hexdigest()
        elif sha and password is not None:
            self.__password = password
        else:
            self.__password = None

    @property
    def passwd(self):
        return self.__password

    @property
    def key(self):
        return b'MXEydzNlNHI1dFQlUiRFI1dAUSE='

    @classmethod
    def __verify_obj(cls, other):
        """
        Verifying objects to membership Password
        :param other: class object
        :return: object or error
        """
        if not isinstance(other, Password):
            raise TypeError("Isn't Password obj")
        else:
            return other

    def __eq__(self, other):
        try:
            verified = self.__verify_obj(other)
            return self.passwd == verified.passwd
        except TypeError:
            print("Only objects of the same class can be compared")
            return None


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
        self.init_db()
        self.read_yaml()

    def init_db(self):
        users = UserDB.get_all_users()
        for user_id in users:
            us = users[user_id]
            password_obj = self.validate_passwd(us["password"], True)
            self.__users[us["login"]] = User(us["login"], password_obj, user_id)

    def read_yaml(self):
        """
        Reads yaml file and adds users obj
        :return: None
        """
        with open(self.users_yaml, "r") as file:
            yml = yaml.load(file, Loader=yaml.FullLoader)
            for types in yml:
                for user in yml[types]:
                    if user["login"] not in self.__users.keys():
                        passwort_obj = self.validate_passwd(user["password"])
                        if passwort_obj.passwd is not None:
                            self.add_user(user["login"], passwort_obj, user["client_id"])

    @staticmethod
    def validate_passwd(password, sha=False):
        """
        Static valid password in sha512
        :param password: password
        :return: Valid password obj
        """
        return Password(password, sha)

    def add_user(self, login, passwd_obj, client_id):
        """
        Adds user obj to users dict
        :param login: login
        :param passwd_obj: valid password obj
        :param client_id: user id
        :return: None
        """
        self.__users[login] = User(login, passwd_obj, client_id)
        user_data = [{
            "id": client_id,
            "login": login,
            "password": passwd_obj.passwd
        }]
        with open("logins_sha.yaml", "a") as yaml_file:
            yaml.dump(user_data, yaml_file)
        try:
            UserDB.add_user(client_id=client_id, login=login, password=passwd_obj.passwd) 
        except Broken_session_DB:
            print(f"write-session to DB with user {login} failed")
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

    def login_att_response(self, input_login, input_password_obj):
        """
        Attemption to log in with response
        :param input_login: user login
        :param input_password_obj: user password obj
        :return: JWT with client id payload - success, False - wrong password, None - unknown login
        """
        try:
            response = self.get_users[input_login].login_attempt(input_password_obj)
            return response
        except KeyError:
            return None

    def check_jwt(self, token):
        """
        Validate JWT token
        :param token: JWT-token
        :return: exception - wrong token, client id - success
        """
        token_id = jwt.decode(token, base64.b64decode(Password().key).decode(), algorithms=["HS256"])["client_id"]
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
            if hash_password.passwd is not None:
                self.add_user(reg_login, hash_password, reg_id)
            else:
                raise WeakPassword
        else:
            raise InaccessibleID


class User:
    """
    Class User
    """

    def __init__(self, login, password_obj, user_id):
        """
        User obj
        :param login: user login
        :param password_obj: password obj
        :param user_id: user id
        """
        self.__login = login
        self.__password = password_obj
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
        us = UserDB.blocking(self.__login)
        self.__block_time = datetime.now() + timedelta(minutes=2)

    @block.deleter
    def block(self):
        self.__blocked = False
        self.__block_time = None
        us = UserDB.blocking(self.__login, False)
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
        return jwt.encode({"client_id": self.user_id}, base64.b64decode(self.passwd.key).decode(), algorithm="HS256")

    def login_attempt(self, input_password_obj):
        """
        Attempt to log in
        :param input_password_obj: password object to validate
        :return: False - wrong password, JWT - success
        """
        if self.block:
            self.check_block()
        if not input_password_obj == self.passwd or self.block:
            self.failure = True
            self.check_fails()
            return False
        else:
            return self.make_jwt()


# Очищаем файл с паролями login_sha.yaml
with open("logins_sha.yaml", "w") as fil:
    fil.write("")

# Создаём объект со всеми пользователями
users = Users("logins.yaml")

# Создаём объект приложения Flask
app = Flask(__name__)


@app.route("/api/v1/identity/login", methods=["POST"])
def app_login():
    """
    Обработка POST-метода для попытки входа
    :return: отправляет ответ с токеном JWT
    """
    request_data = request.json
    try:
        login = request_data["login"]
        password_obj = Password(request_data["password"])
        resp = users.login_att_response(login, password_obj)
        if resp:
            response = make_response({"token": resp})
            response.status = 200
        else:
            response = make_response({
                "status": "error",
                "message": "login or password incorrect"
            })
            response.status = 403
    except KeyError:
        response = make_response({
            "status": "error",
            "message": "required keys are missing"
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
    try:
        token = request_data["token"]
        resp = users.check_jwt(token)
        response = make_response({"client_id": resp})
        response.status = 200
    except KeyError:
        response = make_response({
            "status": "error",
            "message": "required keys are missing"
        })
        response.status = 403
    except WrongToken:
        response = make_response({
            "status": "error",
            "message": "unknown token"
        })
        response.status = 403
    except jwt.exceptions.DecodeError:
        response = make_response({
            "status": "error",
            "message": "token isn't jwt"
        })
        response.status = 403
    return response


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
    except KeyError:
        message = "required keys are missing"
        response = make_response({"status": "error", "message": message})
        response.status = 403
    except WeakPassword:
        message = "incorrect password"
        response = make_response({"status": "error", "message": message})
        response.status = 403
    except InaccessibleID:
        message = f"login and password for client {request_data['client_id']} already exists"
        response = make_response({"status": "error", "message": message})
        response.status = 403
    return response

@app.route("/api/v1/authn/health_check", methods=["GET"])
def health_check():
    response = make_response({"health": "ok"})
    response.status = 200
    return response

app.run(host="0.0.0.0")
