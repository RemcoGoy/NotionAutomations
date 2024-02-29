import os

from dotenv import load_dotenv
from notion_client import Client

load_dotenv()


def authorize_notion():
    notion = Client(auth=os.environ["NOTION_TOKEN"])

    return notion
