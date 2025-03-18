import re
from functools import lru_cache


@lru_cache
def sql_schema():
    all_schema = open("mysql/schema.sql").read()
    pattern = r"-- \<AI\>\n(.*?)\n-- \<\/AI\>"
    schema = "\n".join([
        i.replace("CREATE TABLE", "TABLE")
        for i in re.findall(pattern, all_schema, re.DOTALL)
    ])
    return schema

