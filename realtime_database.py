from typing import Union
from collections.abc import Iterable

import firebase_admin
from firebase_admin import credentials
from pathlib import Path
from firebase_admin import db

from errors import UserAlreadyInDataBase, UserIsNotInDataBase, AutoAdditionToDatabaseIsImmposible
from states import States


def map_error_with_message(func):
    def inside_method(*args, **kwargs):
        try:
            some_data = func(*args, **kwargs)
            return some_data
        except UserAlreadyInDataBase as e:
            print(f"[MAP ERROR TO MESSAGE] Handled error: {type(e)} -> {e}")
            return "User is already in database. No need for addition"
        except UserIsNotInDataBase as e:
            print(f"[MAP ERROR TO MESSAGE] Handled error: {type(e)} -> {e}")
            return "User is not in database or you did not specify some args"
        except AutoAdditionToDatabaseIsImmposible as e:
            print(f"[MAP ERROR TO MESSAGE] Handled error: {type(e)} -> {e}")
            return "When auto_adding_to_database some args where not specified"
        except Exception as e:
            print(f"[MAP ERROR TO MESSAGE] Handled error: {type(e)} -> {e}")
            raise e

    return inside_method


class RealtimeDatabase:
    __is_initialized = False
    __cred = None
    __app = None
    __ref = None

    def __init__(self):
        if RealtimeDatabase.__is_initialized:
            self.cred = RealtimeDatabase.__cred
            self.app = RealtimeDatabase.__app
            self.ref = RealtimeDatabase.__ref
            return

        RealtimeDatabase.__cred = self.cred = credentials.Certificate(
            Path(".") / Path("security") / Path("goto309-private.json"))
        RealtimeDatabase.__app = self.app = firebase_admin.initialize_app(self.cred, {
            'databaseURL': "https://goto309-default-rtdb.europe-west1.firebasedatabase.app/"})
        RealtimeDatabase.__ref = self.ref = db.reference("/")
        RealtimeDatabase.__is_initialized = True

    @map_error_with_message
    def get_database(self) -> object:
        return self.ref.get()

    @map_error_with_message
    def get_user_data(self, telegram_id: Union[str, int]) -> dict:
        telegram_id = str(telegram_id)
        self.check_users_presence_in_database(telegram_id)

        return dict(db.reference(f"/{telegram_id}").get())

    @map_error_with_message
    def add_new_user(self, telegram_id: Union[str, int], telegram_nick: str, full_name: str = None,
                     phone_number: str = None):
        telegram_id = str(telegram_id)
        if self.is_user_in_database(telegram_id):
            raise UserAlreadyInDataBase()
        if isinstance(self.get_database(), dict):
            new_dict = self.get_database()
            new_dict.update({telegram_id: {"state": States.no_state.value, "telegram_nick": telegram_nick,
                                           "full_name": full_name, "phone_number": phone_number,
                                           "number_of_orders": 0}})

            self.ref.set(new_dict)
        else:
            self.ref.set({telegram_id: {"state": States.no_state.value, "telegram_nick": telegram_nick}})

    @map_error_with_message
    def update_user(self, telegram_id: Union[str, int], telegram_nick: str = None, full_name: str = None,
                    phone_number: str = None,
                    number_of_orders: int = 0, auto_add_to_database: bool = False):
        telegram_id = str(telegram_id)
        self.check_users_presence_in_database(telegram_id, auto_add_to_database, telegram_nick)

        user_data = db.reference(f"/{telegram_id}").get()
        if telegram_nick:
            user_data['telegram_nick'] = telegram_nick
        if full_name:
            user_data['full_name'] = full_name
        if phone_number:
            user_data['phone_number'] = phone_number
        if number_of_orders:
            user_data['number_of_orders'] = number_of_orders

        return db.reference(f"/{telegram_id}").set(user_data)

    @map_error_with_message
    def is_user_in_database(self, telegram_id: Union[str, int]) -> Union[str, bool]:
        telegram_id = str(telegram_id)
        if isinstance(self.ref.get(), Iterable) and telegram_id in self.ref.get():
            return True
        return False

    @map_error_with_message
    def get_user_state(self, telegram_id: Union[str, int], auto_add_to_database: bool = False,
                       telegram_nick: str = None) \
            -> Union[str, States]:
        telegram_id = str(telegram_id)
        self.check_users_presence_in_database(telegram_id, auto_add_to_database, telegram_nick)
        state_ = db.reference(f"/{telegram_id}/state").get()
        if state_ is None:
            state_ = States.no_state
            self.set_user_state(telegram_id, States.no_state, True, telegram_nick)
        return States(state_)

    @map_error_with_message
    def set_user_state(self, telegram_id: Union[str, int], state: States, auto_add_to_database: bool = False,
                       telegram_nick: str = None):
        telegram_id = str(telegram_id)
        self.check_users_presence_in_database(telegram_id, auto_add_to_database, telegram_nick)
        return db.reference(f"/{telegram_id}/state").set(state.value)

    @map_error_with_message
    def add_order_to_user(self, telegram_id: Union[str, int], auto_add_to_database: bool = False,
                          telegram_nick: str = None):
        telegram_id = str(telegram_id)
        self.check_users_presence_in_database(telegram_id, auto_add_to_database, telegram_nick)

        self.update_user(telegram_id, number_of_orders=int(
            self.get_user_data(telegram_id).get('number_of_orders', 0)) + 1)

    @map_error_with_message
    def check_users_presence_in_database(self, telegram_id: Union[str, int], auto_add_to_database: bool = False,
                                         telegram_nick: str = None):
        telegram_id = str(telegram_id)
        if not self.is_user_in_database(telegram_id):
            if auto_add_to_database and telegram_id and telegram_nick:
                self.add_new_user(telegram_id, telegram_nick)
            elif auto_add_to_database and (not telegram_id or not telegram_nick):
                raise AutoAdditionToDatabaseIsImmposible()
            else:
                raise UserIsNotInDataBase()
