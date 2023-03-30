import os

from dotenv import load_dotenv
from slack_bolt import App
from classification import classify_question
from inference import get_query_response

from ai import ai_chat_thread, summarize_thread
import posthog

posthog.project_api_key = os.environ.get("POSTHOG_API_KEY")
posthog.host = os.environ.get("POSTHOG_HOST")

CHAT_HISTORY_LIMIT = "20"

load_dotenv()

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

# Add functionality here
# @app.event("app_home_opened") etc
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    try:
        # views.publish is the method that your app uses to push a view to the Home tab
        client.views_publish(
            # the user that opened your app's app home
            user_id=event["user"],
            # the view object that appears in the app home
            view={
                "type": "home",
                "callback_id": "home_view",
                # body of the view
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Welcome to your _App's Home_* :tada:",
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "This button won't do much for now but you can set up a listener for it using the `actions()` method and passing its unique `action_id`. See an example in the `examples` folder within your Bolt app.",
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "Click me!"},
                            }
                        ],
                    },
                ],
            },
        )

    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


def preprocess_slack_thread(bot_id, thread):
    thread = [(msg["user"], msg["text"]) for msg in thread["messages"]]
    history = [{"role": "assistant" if user == bot_id else "user", "content": msg} for user, msg in thread]
    return history


@app.command("/summarize")
def handle_summarize_slash_command(ack, say, command):
    ack()
    send_message(text="Hi there")


@app.event("message")
def handle_message_events(body, logger, say):
    event_type = body["event"]["channel_type"]
    event = body["event"]
    bot_id = body['authorizations'][0]['user_id']
    print(body) 
    if event_type == "im":
        thread = app.client.conversations_history(channel=event["channel"], limit=CHAT_HISTORY_LIMIT)
        thread = preprocess_slack_thread(bot_id, thread)
        response = ai_chat_thread(thread)
        send_message(say, response)

    # new message in a public channel
    elif "thread_ts" not in event and event["type"] == "message" and event["channel_type"] == "channel":
        # follow_up = classify_question(event["text"])

        # if follow_up:
        #     send_message(say, text=response, thread_ts=event["ts"])
        return
    # thread response in a public channel
    elif "thread_ts" in event and event["channel_type"] == "channel":
        return 
        thread_ts = event["thread_ts"]
        # Call the conversations.replies method with the channel ID and thread timestamp
        # try:
        result = app.client.conversations_replies(channel=event["channel"], ts=thread_ts)
        messages = result["messages"]

        thread = preprocess_slack_thread(bot_id, result)

        # except Exception as e:
        #     print("Error retrieving thread messages: {}".format(e))
        #     return

        if "assistant" not in [msg["role"] for msg in thread]:
            # we haven't responded and it's a thread, which meant the classification said no, so don't try to respond
            return

        if len(thread) >= 4:
            # This is too long, not worth responding to
            return

        if thread[-1]["role"] == "assistant":
            # we just responded, don't respond to ourselves
            return
        
        # get first message in thread
        question = thread[0]["content"]
        response = get_query_response(question, thread)

        send_message(say, text=response, thread_ts=event["thread_ts"])

@app.event("emoji_changed")
def handle_emoji_changed_events(body, logger, say):
    print(body)


@app.event("app_mention")
def handle_app_mention_events(body, logger, say):
    logger.info(body)
    print(body)
    bot_id = body['authorizations'][0]['user_id']
    event = body["event"]
    thread_ts = event["thread_ts"] if "thread_ts" in event else event["ts"]
    thread = app.client.conversations_replies(
        channel=event["channel"], ts=thread_ts, limit=CHAT_HISTORY_LIMIT
    )
    if "please summarize this" in event["text"].lower():
        send_message(say, text="On it!", thread_ts=thread_ts)
        summary = summarize_thread(thread)
        send_message(say, text=summary, thread_ts=thread_ts)
        return
    

    thread = preprocess_slack_thread(bot_id, thread)
    response = ai_chat_thread(thread)
    send_message(say, text=response, thread_ts=thread_ts)

def send_message(say, text, thread_ts):
    posthog.capture("max", "message generated", {"message": text, "thread_ts": thread_ts})
    if thread_ts:
        say(text=text, thread_ts=thread_ts)
    else:
        say(text)


# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
