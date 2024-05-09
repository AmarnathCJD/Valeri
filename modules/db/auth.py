from modules.db.db import DB, DB_MODE

ADMINS = []


def is_auth(user_id):
    """
    Check if a user is authorized.
    """
    return user_id in ADMINS


def add_auth(user_id):
    """
    Add a user to the list of authorized users.
    """
    # create table if not exists -
    DB.execute("CREATE TABLE IF NOT EXISTS auth (user_id INTEGER PRIMARY KEY)")
    if user_id not in ADMINS:
        ADMINS.append(user_id)
        if DB_MODE == "sql":
            DB.execute("INSERT INTO auth (user_id) VALUES (?)", (user_id,))
        else:
            DB.main.update_one(
                {"_id": "auth"}, {"$push": {"admins": user_id}}, upsert=True
            )
        return True
    return False


def remove_auth(user_id):
    """
    Remove a user from the list of authorized users.
    """
    DB.execute("CREATE TABLE IF NOT EXISTS auth (user_id INTEGER PRIMARY KEY)")
    if user_id in ADMINS:
        ADMINS.remove(user_id)

        if DB_MODE == "sql":
            DB.execute("DELETE FROM auth WHERE user_id = ?", (user_id,))
        else:
            DB.main.update_one(
                {"_id": "auth"}, {"$pull": {"admins": user_id}}, upsert=True
            )
        return True
    return False


def get_auth():
    """
    Get the list of authorized users.
    """
    return ADMINS


def __init_auth():
    """
    Initialize the list of authorized users.
    """
    global ADMINS
    if DB_MODE == "sql":
        admins = DB.execute("SELECT user_id FROM auth")
        if admins:
            ADMINS.extend([admin[0] for admin in admins])
    else:
        admins = DB.main.find_one({"_id": "auth"})
        if admins:
            ADMINS.extend(admins["admins"])


# __init_auth()
