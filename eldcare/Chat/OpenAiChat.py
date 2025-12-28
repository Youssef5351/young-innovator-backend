from openai import OpenAI
from config import firebase_config
from datetime import datetime
import pytz
import dotenv

import firebase_admin
from firebase_admin import credentials, db as admin_db

if not firebase_admin._apps:  # Only initialize if no app exists
    cred = credentials.Certificate(firebase_config["serviceAccount"])
    firebase_admin.initialize_app(cred, {
        "databaseURL": firebase_config["databaseURL"]
    })

db = admin_db.reference()


OPEN_AI_KEY = dotenv.get_key('.env', 'OPEN_AI_KEY')


def get_schedule_answer(userInput, userId):
    client = OpenAI(api_key=OPEN_AI_KEY)

    # 🔁 same data structure as pyrebase
    data = db.child("schedule").child(userId).get()

    events_by_date = {}
    schedule = ""

    if not data:
        schedule = "No events found.\n"
    else:
        for event in data.values():
            start_date = datetime.fromisoformat(event['startDate'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(event['endDate'].replace('Z', '+00:00'))

            start_date = start_date.astimezone(pytz.timezone('US/Eastern'))
            end_date = end_date.astimezone(pytz.timezone('US/Eastern'))

            date_str = start_date.strftime('%d-%m-%Y')
            time_str = f"{start_date.strftime('%I:%M %p')} - {end_date.strftime('%I:%M %p')}"

            if date_str not in events_by_date:
                events_by_date[date_str] = []

            events_by_date[date_str].append(f"{time_str}: {event['title']}")

        for date, events in events_by_date.items():
            schedule += f"{date}\n"
            for event in events:
                schedule += f"{event}\n"
            schedule += "\n"

    print(schedule)

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a nurse/ assistant for an elderly person. "
                    "You need to be able to answer questions about the elderly person's schedule "
                    "strictly from the schedule given below. "
                    "Today's date is 28-01-2024. "
                    "If there is no appointment today, say the schedule is free. "
                    "Don't make things up."
                )
            },
            {"role": "assistant", "content": "Schedule is:\n" + schedule},
            {"role": "user", "content": userInput}
        ],
        temperature=0.2,
    )

    return completion.choices[0].message.content


def get_general_answer(userInput):
    client = OpenAI(api_key=OPEN_AI_KEY)

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a nurse/ assistant for an elderly person. "
                    "Answer general questions cheerfully and factually. "
                    "If you don't know the answer, say you don't know."
                )
            },
            {"role": "user", "content": userInput}
        ],
    )

    return completion.choices[0].message.content


def set_reminder(input_text):
    client = OpenAI(api_key=OPEN_AI_KEY)

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You help a computer function set a reminder. "
                    "Answer strictly in this format:\n"
                    "[startTime, endTime, title]\n\n"
                    "Example:\n"
                    "[2024-02-26T18:30:00.000Z, 2024-02-26T19:30:00.000Z, perform certain task]\n\n"
                    "Today's date and time is 2024-01-28T06:30:00.000Z"
                )
            },
            {"role": "user", "content": input_text}
        ],
        temperature=0.1,
    )

    return completion.choices[0].message.content
