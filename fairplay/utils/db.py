from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement


class ServerUUID(FunctionElement):
    name = "uuid"


@compiles(ServerUUID)
def compile_uuid(element, compiler, **kwargs):
    return """select substr(u,1,8)||'-'||substr(u,9,4)||'-4'||substr(u,13,3)||
  '-'||v||substr(u,17,3)||'-'||substr(u,21,12) from (
    select lower(hex(randomblob(16))) as u,
    substr('89ab',abs(random()) % 4 + 1, 1) as v);"""


@compiles(ServerUUID, "postgresql")
def compile_uuid_postgresql(element, compiler, **kwargs):
    return "uuid_generate_v4()"
