from sqlalchemy import event, inspect
from app.models.user_tables import User
from app.core.hash import hash_value

HASH_FIELDS = {
    "email": "hashed_email",
    "username": "hashed_username",
    "mobile": "hashed_mobile",
}

@event.listens_for(User, "before_insert")
def user_before_insert(mapper, connection, target: User):
    for plain_field, hash_field in HASH_FIELDS.items():
        value = getattr(target, plain_field, None)
        if value:
            setattr(target, hash_field, hash_value(value))


@event.listens_for(User, "before_update")
def user_before_update(mapper, connection, target: User):
    state = inspect(target)

    for plain_field, hash_field in HASH_FIELDS.items():
        hist = state.attrs[plain_field].history
        if hist.has_changes():
            value = getattr(target, plain_field)
            setattr(target, hash_field, hash_value(value))
