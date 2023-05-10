from datetime import datetime, timedelta

import csv
import json
import time
import yaml
import os


def get_users_from_json(json_file: str):
    """
    Get users info from json-file
    :param json_file: name or path to json file
    :return: list with users dictionaries
    """
    users_list = []
    with open(json_file, "r") as file:
        js = json.load(file)
        for user in js["users"]:
            if validate_passwd(user['password']):
                users_list.append({"id": user["id"], "login": user["login"], "password": user["password"]})
    return users_list


def get_users_from_yaml(yaml_file: str):
    """
    Get users info from yaml-file
    :param yaml_file: name or path to yaml file
    :return: list with users dictionaries
    """
    users_list = []
    with open(yaml_file, "r") as file:
        yml = yaml.load(file, Loader=yaml.FullLoader)
        for user in yml["users"]:
            if validate_passwd(user['password']):
                users_list.append({"id": user["id"], "login": user["login"], "password": user["password"]})
    return users_list


def validate_passwd(password: str):
    """
    Validation password
    :param password: password
    :return: if valid returns True, else returns False
    """
    if len(password) < 8:
        return False
    elif password.isupper() or password.islower() or password.isdigit():
        return False
    elif not any(ch.isdigit() for ch in password):
        return False
    else:
        return True


def validate_user(users_list: list, login: str, passwd: str):
    """
    User validation
    :param users_list: list with users dictionaries
    :param login: login
    :param passwd: password
    :return: True if unknown user login, False if wrong password and user id if validation successfully
    """
    out = True
    for user in users_list:
        if user["login"] == login:
            if user["password"] == passwd:
                out = user["id"]
            else:
                out = False
    return out


def check_block_timeout(blocked_users: dict):
    """
    Check block timeout for user
    :param blocked_users: dict with blocked users
    :return: list with user logins to remove from blocked users
    """
    time_now = datetime.now()
    delete_keys = []
    for key, block_time in blocked_users.items():
        if block_time < time_now:
            delete_keys.append(key)
    return delete_keys

#Получаем список всех пользователей
users = [*get_users_from_json("users.json"), *get_users_from_yaml("users.yaml")]

#Создаем 2 словаря с попытками и заблокированными пользователями
retryes = {user["login"]: 3 for user in [us for us in users]}
blocked_users = {}

#Запускаем бесконечный цикл проверки файла с пользователями
while True:
    time.sleep(1)
    #Проверка на наличие в csv-файле новых записей
    if os.stat("input.csv").st_size != 0:
        #Проверяем на наличие заблокированных пользователей
        if len(blocked_users) > 0:
            #Получаем список пользователей, которых стоит разблокировать
            keys = check_block_timeout(blocked_users)
            #Проверяем, есть ли пользователи для разблокировки и разблокируем их при наличии
            if len(keys) > 0:
                for key in keys:
                    del blocked_users[key]
                    retryes[key] = 3
        #Открываем файл для чтения и считываем новые записи
        with open("input.csv", "r") as file:
            csv_read = csv.reader(file)
            #Проходимся построчно по файлу
            for user in csv_read:
                #Проверяем на статус пользователя, если он не заблокирован, то проводим валидацию
                if user[0] not in blocked_users.keys():
                    #Получаем флаг, который говорит о статусе валидации введеных данных
                    flag = validate_user(users, user[0], user[1])
                    match flag:
                        #Первым проверяем, есть ли пользователь
                        case True:
                            print("Неверный пользователь или пароль")
                        #Вторым проверяем на неправильный пароль. Уменьшаем количество попыток и если оно становится =0, то блокируем пользователя
                        case False:
                            print("Неверный пользователь или пароль")
                            retryes[user[0]] -= 1
                            if retryes[user[0]] == 0:
                                blocked_users[user[0]] = datetime.now() + timedelta(minutes=2)
                        #Приветствуем залогинившегося пользователя по id при прохождении всех проверок
                        case _:
                            print(f"Привет {flag}")
                else:
                    #Выводим сообщение о том, что пользователь заблокирован, если он находится в блокировке

                    print("Пользователь заблокирован")
        #Запускаем цикл для очистки csv после проведения валидации. Цикл ожидает момент, когда файл будет разрешген к редактированию
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