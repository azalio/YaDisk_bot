from pymongo import MongoClient
import logging
import datetime


def mongo_connect(host, port, db, collection):
    """
    Connecting to mongo.
    :param host: 
    :param port: 
    :param db: 
    :param collection: 
    :return: 
    """
    client = MongoClient(host, port)
    db = client[db]
    collection = db[collection]
    return client, db, collection


# def check_id(m_id, collection):
#     """
#     Check what user exist
#     :param m_id:
#     :param collection:
#     :return:
#     """
#     if collection.find({"_id": m_id}).count() == 1:
#         return False
#     else:
#         return True


def check_user_id(user_id, collection):
    """
    Check user or create new.
    :param user_id: 
    :param collection: 
    :return: If exits - OAuth token, if user in status prepare - return 1 as flag ( for getting OAuth again )
    """
    cursor = collection.find_one({"user_id": user_id, "status": "complete"}, {"_id": 0, "user_id": 0})
    if cursor is not None:
        return cursor['ya_disk_oauth']
    else:
        cursor = collection.find_one({"user_id": user_id, "status": "prepare"})
        if cursor is None:
            cursor = collection.insert_one({'user_id': user_id, 'status': 'prepare'})
        if cursor is not None:
            return 1


def delete_user(user_id, collection):
    """
    Delete user.
    :param user_id: 
    :param collection: 
    :return: 
    """
    cursor = collection.delete_one({"user_id": user_id})
    if cursor.deleted_count == 1:
        return True
    else:
        return False


def update_user_oauth(user_id, text, collection):
    """
    Update OAuth token.
    :param user_id: 
    :param text: 
    :param collection: 
    :return: 
    """
    result = collection.update_one({"user_id": user_id}, {"$set": {"status": "complete", "ya_disk_oauth": text}})
    if result.matched_count == 1:
        return True
    else:
        return False


def update_last_file(user_id, collection, path):
    """
    Update name of last upload file.
    :param user_id: 
    :param collection: 
    :param path: 
    :return: 
    """
    result = collection.update_one({"user_id": user_id}, {"$set": {"last_file_path": path}})
    if result.matched_count == 1:
        return True
    else:
        return False


def update_user_info(user_id, collection, **kwargs):
    """
    Add +1 if user upload file.
    :param user_id: 
    :param collection: 
    :param kwargs: 
    :return: 
    """
    kwargs['lastdate'] = datetime.datetime.utcnow()
    result = collection.update_one({"user_id": user_id}, {
        "$set": kwargs,
        "$inc": {"count": 1}})
    logging.debug(result.raw_result)
    if result.matched_count == 1:
        return True
    else:
        return False


def get_user_last_file(user_id, collection):
    """
    For share file.
    :param user_id: 
    :param collection: 
    :return: 
    """
    cursor = collection.find_one({"user_id": user_id, "status": "complete"}, {"_id": 0, "user_id": 0})
    if cursor is not None:
        return [cursor['ya_disk_oauth'], cursor['last_file_path']]
    else:
        return False
