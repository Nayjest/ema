import json
from time import sleep

import microcore as mc
import re

from microcore import ui
from sqlalchemy import text

import ema.env as env
import ema.db as db
from ema.tools import sql_schema

def extract_xml_tags(text: str) -> list[tuple[str, str]]:
    """
    Extracts all XML tags and their content from a given text string.

    Args:
        text (str): The text containing XML-like tags.

    Returns:
        list[tuple[str, str]]: A list of tuples where each tuple contains a tag name and its content.
    """
    matches = re.findall(r"<(\w+)>(.*?)</\1>", text, re.DOTALL)
    return [(tag, content.strip()) for tag, content in matches]

def extract_xml_tag(text: str) -> tuple[str, str] | None:
    """
    Extracts the first XML tag and its content from a given text string.

    Args:
        text (str): The text containing XML-like tags.

    Returns:
        tuple[str, str] | None: A tuple containing the tag name and its content, or None if no match is found.
    """
    match = re.search(r"<(\w+)>(.*?)</\1>", text, re.DOTALL)
    if match:
        return match.group(1), match.group(2).strip()
    return None, None


def answer(question: str, user: str):
    history = [
        mc.SysMsg(mc.tpl(
            "answer_2.j2",
            linear_gql_schema=mc.storage.read("linear_schema_min_compact.txt"),
            question=question,
            user=user,
            sql_schema = sql_schema()
        )),
    ]
    i = 0
    while True:
        i+=1
        if i > 10:
            print(ui.red("Too many iterations!"))
            break
        if i > 1:
            sleep(10)
        ai_response: str = mc.llm(history)
        history.append(mc.AssistantMsg(ai_response))
        tags = extract_xml_tags(ai_response)

        ended=False
        sys_answer = "{System}: continue with the next step"
        for tag,content in tags:

            if tag == "result":
                print(ui.yellow(content))
                ended=True
                break
            if tag == "think":
                continue
            if tag == "linear_gql":
                try:
                    data = env.linear_api.request(content)
                except Exception as e:
                    sys_answer = str(e)
                    continue
                sys_answer = "Returned data:\n"+json.dumps(data)
                continue
            if tag == "sql":
                print(ui.magenta("SQL:"+content))
                try:
                    # Execute the SQL query
                    with db.session() as ses:
                        result = ses.execute(text(content))
                        rows = result.fetchall()

                        # Format the result as a string
                        result_str = "Query result:\n" + "\n".join([str(row) for row in rows])
                        print(ui.yellow(result_str))
                        sys_answer=result_str
                except Exception as e:
                    sys_answer=f"SQL Error: {str(e)}"
                    print(ui.red(sys_answer))
                    continue
        if ended:
            break
        else:
            history.append(mc.UserMsg(sys_answer))

