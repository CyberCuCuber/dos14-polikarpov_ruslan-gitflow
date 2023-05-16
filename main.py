from datetime import datetime, timedelta
import hashlib
import yaml
import time
import os
import csv


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
        self.users_yaml = users_yaml
        self.__blocked_users = []
        self.read_yaml()

    def read_yaml(self):
        """
        Reads yaml file and adds users obj
        :return: None
        """
        with open(self.users_yaml, "r") as file:
            yml = yaml.load(file, Loader=yaml.FullLoader)
            print(yml)
            for types in yml:
                for user in yml[types]:
                    if self.validate_passwd(user["password"]) is not None:
                        passwd = Password(user["password"]).passwd
                        self.add_user(user["login"], passwd, user["entity_id"])

    @staticmethod
    def validate_passwd(password):
        """
        Static valid password in sha512
        :param password: password
        :return: Valid password in sha512
        """
        return Password(password).passwd

    def add_user(self, login, passwd, entity_id):
        """
        Adds user obj to users dict
        :param login: login
        :param passwd: valid password in sha512
        :param entity_id: user id
        :return: None
        """
        self.__users[login] = User(login, passwd, entity_id)

    @property
    def get_users(self):
        return self.__users

    @property
    def blocked_users(self):
        return self.__blocked_users

    @blocked_users.setter
    def blocked_users(self, login):
        self.__blocked_users.append(login)

    def del_block(self, login):
        """
        Deletes blocking for user
        :param login: user login
        :return: None
        """
        self.__blocked_users.remove(login)

    def check_blocked_users(self):
        """
        Checking bloked users
        :return: None
        """
        if len(self.__blocked_users):
            for us in self.__blocked_users:
                if self.__users[us].check_block():
                    self.del_block(us)


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

    def add_failure(self):
        """
        Adding failure attempt to validate credentials
        :return: True if too many fails and False if fails count <3
        """
        self.__failure_cont += 1
        return self.check_fails()

    @failure.deleter
    def failure(self):
        """
        Reset failure count
        :return: None
        """
        self.__failure_cont = 0

    def check_fails(self):
        """
        Checks failure count and block user if too many fails make
        :return: True if too many fails and False if fails count <3
        """
        if self.__failure_cont >= 3:
            self.block = True
            return True
        else:
            return False

    def check_block(self):
        """
        Checks if the user is locked out and unlocks if the lock timeout expires
        :return: True if the user is locked out, False if the user is still locked out
        """
        if datetime.now() >= self.__block_time:
            del self.block
            return True
        else:
            return False


if __name__ == "__main__":
    # Создаём объект пользователей из файла yaml
    users = Users("logins.yaml")
    while True:
        time.sleep(1)
        # Проверка на наличие в csv-файле новых записей
        if os.stat("input.csv").st_size != 0:
            # Проверяем на наличие заблокированных пользователей и разблокируем при необходимости
            users.check_blocked_users()
            # Открываем файл для чтения и считываем новые записи
            with open("input.csv", "r") as file:
                csv_read = csv.reader(file)
                # Проходимся построчно по файлу
                for user in csv_read:
                    # Проверяем на статус пользователя, если он не заблокирован, то проводим валидацию
                    logged_user = user[0]
                    # Проверяем, нет ли пользователя в списке заблокированных
                    if logged_user not in users.blocked_users:
                        # Проверяем наличие пользователя в базе
                        if logged_user in users.get_users.keys():
                            # Хешируем пароль
                            password = hashlib.sha512(user[1].encode()).hexdigest()
                            # Проверяем, совпадает ли пароль
                            if password != users.get_users[logged_user].passwd:
                                # Проверка количества ошибок
                                if users.get_users[logged_user].add_failure():
                                    users.blocked_users = logged_user
                                print("Неверный пользователь или пароль")

                            else:
                                print(f"Привет {users.get_users[logged_user].user_id}")
                        else:
                            print("Пользователь не найден")
                    else:
                        print("Пользователь заблокирован")
            # Запускаем цикл для очистки csv после проведения валидации. Цикл ожидает момент, когда файл будет разрешен к редактированию
            a = True
            while a:
                time.sleep(1)
                try:
                    with open("input.csv", "w") as file:
                        file.write("")
                    print("Файл очищен")
                    a = False
                except PermissionError:
                    a = True
                    print("Файл пока занят")
        else:
            print("Нет записей")
