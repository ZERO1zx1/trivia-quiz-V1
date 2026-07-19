"""Room Service"""
import random
import string
from app.models.room import Room, RoomPlayer
from app.extensions import db

class RoomService:
    @staticmethod
    def generate_code(length=6):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            if not Room.query.filter_by(code=code).first():
                return code

    @staticmethod
    def can_join(room, user_id, password=None):
        if room.status != 'waiting':
            return False, 'Room is not accepting players'
        if room.is_full():
            return False, 'Room is full'
        existing = RoomPlayer.query.filter_by(room_id=room.id, user_id=user_id).first()
        if existing:
            return True, None
        if room.is_private and room.password != password:
            return False, 'Incorrect password'
        return True, None
