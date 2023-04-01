import datetime
import os

from pprint import pprint

from dotenv import load_dotenv
from pdpyras import APISession, PDClientError


load_dotenv()


api_key = os.environ.get('PD_API_KEY')
session = APISession(api_key, default_from="max.ai@posthog.com")


def get_all_schedule_ids_and_names():
    schedules = []
    offset = 0
    limit = 100  # Maximum limit allowed by PagerDuty API
    while True:
        try:
            response = session.get("schedules", params={"limit": limit, "offset": offset}).json()
            if not response.get("schedules", []):
                break

            for schedule in response["schedules"]:
                schedules.append((schedule["id"], schedule["summary"]))

            offset += limit
        except PDClientError as e:
            print(f"Error: {e}")
            break

    return schedules


def get_current_oncalls(schedule_id):
    try:
        oncalls = session.get("oncalls", params={
            "schedule_ids[]": schedule_id,
            "since": datetime.datetime.now().isoformat(),
            "until": datetime.datetime.now().isoformat()
        }).json()

        return [oncall['user'] for oncall in oncalls['oncalls']]
    except PDClientError as e:
        print(f"Error: {e}")
        return []


def current_oncalls():
    oncalls = {} 
    for schedule_id, schedule_name in get_all_schedule_ids_and_names():
        oncall_users = get_current_oncalls(schedule_id)
        if len(oncall_users) < 1:
            continue 
        oncalls[schedule_name] = []
        for user in oncall_users:
            summary = user.get('summary', 'no summary')
            email = user.get('email', 'no email')
            oncalls[schedule_name].append(summary)
    return oncalls 

def build_oncall_prompt():
    oncalls = current_oncalls() 
    prompt = ["Current oncalls (people responsible for certain areas): "]
    for schedule in oncalls:
        prompt.append(f"{schedule}: {', '.join(oncalls[schedule])}")
    return "\n".join(prompt)


if __name__ == "__main__":
    print(build_oncall_prompt())
