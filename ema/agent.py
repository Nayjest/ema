import json
from time import sleep

import microcore as mc
import re

from microcore import ui

import ema.env as env

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

# Example usage:
text = "<note>Hello, this is an XML content!</note>"
print(extract_xml_tag(text))  # Output: ('note', 'Hello, this is an XML content!')

def answer(question: str):
    history = [
        mc.SysMsg(mc.tpl(
            "answer_user_question.j2",
            linear_gql_schema=mc.storage.read("linear_schema_min_compact.txt"),
            question=question
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
        answer: str = mc.llm(history)
        history.append(mc.AssistantMsg(answer))
        tag, content = extract_xml_tag(answer)
        if tag == "answer":
            print(ui.yellow(content))
            break
        if tag == "think":
            history.append(mc.UserMsg("[SYSTEM]: Please continue"))
            continue
        if tag == "linear_gql":
            try:
                data = env.linear_api.request(content)
            except Exception as e:
                history.append(mc.UserMsg(str(e)))
                continue
            history.append(mc.UserMsg(json.dumps(data)))
            continue
        print(ui.red(f"Invalid XML tag found in the answer! {tag}"))
        break
