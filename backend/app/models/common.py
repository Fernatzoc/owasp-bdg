from typing import Any, Annotated
from bson import ObjectId
from pydantic import BeforeValidator, PlainSerializer

def validate_object_id(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str) and ObjectId.is_valid(v):
        return v
    if v is None:
        return None
    raise ValueError("ObjectId no válido")

PyObjectId = Annotated[
    str,
    BeforeValidator(validate_object_id),
    PlainSerializer(lambda x: str(x), return_type=str)
]
