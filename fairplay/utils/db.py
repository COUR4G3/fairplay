from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement


class ServerUUID(FunctionElement):
    name = "uuid"


@compiles(ServerUUID)
def compile_uuid(element, compiler, **kwargs):
    return (
        "lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || "
        "'-4' || substr(lower(hex(randomblob(2))),2) || '-' || "
        "substr('89ab',abs(random()) % 4 + 1, 1) || "
        "substr(lower(hex(randomblob(2))),2) || '-' || "
        "lower(hex(randomblob(6)))"
    )


@compiles(ServerUUID, "postgresql")
def compile_uuid_postgresql(element, compiler, **kwargs):
    return "uuid_generate_v4()"
