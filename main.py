id_login= [
    '1_rhob_citsimitpo',
    '3_artskjid_suoicipsus',
    '5_arihimaharav_ymaerd',
    '10_erak_gniyfitsym',
    '2_nella_ypeels',
    '7_htunk_gnihgual',
    '4_rekarbenots_yrgnuh',
    '6_temmas_tnerever',
    '8_araksahb_cipe',
    '9_ekip_ciots',
]
id_pass = [
    '1_DQsUxHgy9kEE6upe688ifc9MBO2lkcLc',
    '2_cJvzT0s8poVTjvhF34BQmZFAcvhGmKPn',
    '3_tm4ULFqMO2Tzt3UkzYIHw1xk860XLTQa',
    '4_XVesS2w42en15zMcgzaJk5BubK0A8EWd',
    '5_yg0Ldi2uchFC5iXlFKE0QB2WJoEtenwK',
    '6_wDBhQlOhNTw9jhjOm8jIy7xRVdP3bSID',
    '7_X3PZukCAyG2CAGT5q8kxEDzwb81x56JV',
    '8_bZFqop2Pwg83gg3pWs4VUs9OLdq0XaBU',
    '9_fqMYpqWVwn0njtl7wcjjWGLrOdYchyml',
    '10_2lfeAUoR4nYz0VSr3IhEm8h2GFQLFMzh'
]

def sortById(input_str):
    return int(input_str.split("_", 1)[0])

def get_users_dicts(id_login: list, id_pass: list):
    """
    Getting list with users dicts
    :param id_login: list with elements type 'id_login'. 'login' reversed
    :param id_pass: list with elements type 'id_password'. 'password' reversed
    :return: list with dicts like {id: id, login: login, password: password}
    """
    users = []
    try:
        if len(id_login) != len(id_pass):
            raise ValueError
        id_login.sort(key=sortById)
        id_pass.sort(key=sortById)
        len_list = len(id_login)
        list_ids = [int(i.split("_", 1)[0]) for i in id_pass]
        for count in range(len_list):
            users.append(
                {
                    "id": list_ids[count],
                    "login": id_login[count].split("_",1)[1][::-1],
                    "password": id_pass[count].split("_",1)[1][::-1] 
                }
            )
        return users
    except ValueError:
        print("One of the input lists is missing fields")
    except Exception as ex:
        print(f"Something other wrong\n{ex}")


if __name__ == "__main__":
    
     users_list = get_users_dicts(id_login, id_pass)
     for user_dict in users_list:
        print(user_dict)

