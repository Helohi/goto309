from enum import Enum


class States(Enum):
    no_state = "no_state"
    waiting_name = "waiting_name"
    waiting_phone_number = "waiting_phone_number"
    waiting_payment = "waiting_payment"
    on_moderation = "on_moderation"
    waiting_feedback = "waiting_feedback"

