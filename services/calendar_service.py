from flask import session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta


def get_calendar_service():

    token = session.get("google_token")

    if not token:
        raise Exception("User is not authenticated with Google.")

    creds = Credentials(
        token=token["access_token"]
    )

    return build(
        "calendar",
        "v3",
        credentials=creds
    )


def get_upcoming_events(max_results=100):

    service = get_calendar_service()

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        )
        .execute()
    )

    events = events_result.get("items", [])

    print(f"Found {len(events)} events")

    return events


def create_calendar_event(title, description, deadline):

    service = get_calendar_service()

    start = datetime.fromisoformat(deadline)

    end = start + timedelta(hours=1)

    event = {
        "summary": title,
        "description": description,
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {
                    "method": "popup",
                    "minutes": 1440
                },
                {
                    "method": "popup",
                    "minutes": 60
                },
                {
                    "method": "popup",
                    "minutes": 15
                }
            ]
        }
    }

    created_event = (
        service.events()
        .insert(
            calendarId="primary",
            body=event
        )
        .execute()
    )

    return created_event["id"]