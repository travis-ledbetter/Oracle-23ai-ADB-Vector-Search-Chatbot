from __future__ import print_function
from llama_index.core.llms import ChatMessage
from urllib.request import urlopen
from streamlit_cookies_controller import CookieController
import re as r
import streamlit as st
import json
import uuid
import pickle
import requests
import oracledb

from config import(
    DB_USER,
    DB_PWD,
    DSN,
    CONFIG_DIR,
    WALLET_LOCATION,
    WALLET_PASSWORD
)

def CheckForHistory():
    controller = CookieController()

    user_id = controller.get('vector_db_chat_history')
    if user_id:
        return user_id
    else:
        return False

def StoreChatHistory(user_id = None, history = None):
    if not history:
        return

    connection = oracledb.connect(
        user=DB_USER,
        password=DB_PWD,
        config_dir=CONFIG_DIR,
        dsn=DSN,
        wallet_location=WALLET_LOCATION,
        wallet_password=WALLET_PASSWORD
)

    if not user_id:
        random_uuid = str(uuid.uuid4())[:12]
        data = []
        data_user = serialize(history[len(history)-2])
        data_ai = serialize(history[len(history)-1])
        data.append(data_user)
        data.append(data_ai)

        controller = CookieController()
        controller.set('vector_db_chat_history',random_uuid)
        pickled_data = pickle.dumps(data)
        cursor = connection.cursor()
        cursor.execute("insert into vector_chat_history values (:num,:hist)",[random_uuid,pickled_data])
        connection.commit()
        cursor.close()
    else:
        cursor = connection.cursor()
        cursor.execute("select history from vector_chat_history where uuid = :num",[user_id])

        row = cursor.fetchone()
        row = row[0].read()
        data = pickle.loads(row)


        data_user = serialize(history[len(history)-2])
        data_ai = serialize(history[len(history)-1])
        data.append(data_user)
        data.append(data_ai)

        pickled_data = pickle.dumps(data)
        cursor.execute("update vector_chat_history set history = :hist where uuid = :num",[pickled_data,user_id])
        connection.commit()
        cursor.close()

    connection.close()

def serialize(obj):
    if not isinstance(obj,ChatMessage):
        return
    else:
        new_obj = {
            "role": obj.role,
            "content": obj.content,
            "additional_kwargs": obj.additional_kwargs
        }
        return new_obj
