import os
from typing import List

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm

from auth.google_auth import authorize_google
from auth.notion_auth import authorize_notion

load_dotenv()

SHEET_ID = os.getenv("SHEET_ID")
RANGE = os.getenv("RANGE")

DB_ID = os.getenv("DB_ID")


def sync_laptimes():
    google_creds = authorize_google()
    notion_client = authorize_notion()

    try:
        service = build("sheets", "v4", credentials=google_creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE).execute()
        values: List[List[str]] = result.get("values", [])

        if not values:
            print("No data found.")
            return

        track_results = notion_client.databases.query(
            **{
                "database_id": DB_ID,
            }
        )

        existing_tracks = list(
            map(
                lambda x: x["properties"]["Name"]["title"][0]["plain_text"],
                track_results["results"],
            )
        )

        header = values.pop(0)
        timing_props = header[3:]

        for row in tqdm(values):
            track_name = row[0].strip("**")

            track_index = (
                existing_tracks.index(track_name)
                if track_name in existing_tracks
                else -1
            )

            timing_properties = {
                prop: {"rich_text": [{"text": {"content": row[header.index(prop)]}}]}
                for prop in timing_props
            }

            if track_index == -1:
                # New entry
                notion_client.pages.create(
                    parent={"database_id": DB_ID},
                    properties={
                        "Name": {"title": [{"text": {"content": track_name}}]},
                        **timing_properties,
                    },
                )
            else:
                # Update
                existing_track = track_results["results"][track_index]
                page_id = existing_track["id"]

                notion_client.pages.update(page_id, properties={**timing_properties})

    except HttpError as err:
        print(err)


sync_laptimes()
