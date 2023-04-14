import os
import traceback

import posthoganalytics as posthog
from dotenv import load_dotenv
from slack_bolt.async_app import AsyncApp

from ai import ai_chat_thread, summarize_thread
from inference import get_query_response

CHAT_HISTORY_LIMIT = 20

load_dotenv()

posthog.project_api_key = os.environ.get("POSTHOG_API_KEY")
posthog.host = os.environ.get("POSTHOG_HOST")

# Initializes your app with your bot token and signing secret
app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

# Add functionality here
# @app.event("app_home_opened") etc
@app.event("app_home_opened")
async def update_home_tab(client, event, logger):
    try:
        # views.publish is the method that your app uses to push a view to the Home tab
        await client.views_publish(
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
                            "text": "*Hi there! I'm Max!* :wave:",
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Hello! As PostHog's trusty support AI, I'm happy to answer any questions you may have about PostHog. If you're curious about our product, features, or pricing, I'm here to help. As an open-source company, we want to provide an excellent user experience, and we're always happy to receive feedback. If you have any suggestions, please let us know.\n\n *How to interact with Max* \n It's simple. Just @ mention @max_ai in any thread and ask what you would like done. Examples may look like:\n- @max_ai can you try answering the question here?\n- @max_ai can you summarize this?\n- @max_ai I have a question about <something awesome>\n- @max_ai Who is the current support hero that I can talk to about this? \n\n *How does max work?!*\nYou can find out more about how Max is built on GitHub!\nhttps://github.com/posthog/max-ai\nOf course it's Open Source :hog-excited:\n\n*Disclaimer!*\n_Max may display inaccurate or offensive information that doesn’t represent PostHog's views._\nThis is the case with LLMs in the current state. We try our best here to have a system prompt that keeps Max on topic.\nFeel free to question and chat with Max but do keep in mind that this is experimental.",
                        },
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
async def handle_summarize_slash_command(ack, say, command):
    ack()
    await send_message(text="Hi there")


@app.event("message")
async def handle_message_events(body, logger, say):
    event_type = body["event"]["channel_type"]
    event = body["event"]
    bot_id = body['authorizations'][0]['user_id']
    print(body) 
    if event_type == "im":
        thread = await app.client.conversations_history(channel=event["channel"], limit=CHAT_HISTORY_LIMIT)
        thread = preprocess_slack_thread(bot_id, thread)
        response = await ai_chat_thread(thread)
        await send_message(say, response)

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
        result = await app.client.conversations_replies(channel=event["channel"], ts=thread_ts)
        result["messages"]

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

        await send_message(say, text=response, thread_ts=event["thread_ts"])

@app.event("emoji_changed")
async def handle_emoji_changed_events(body, logger, say):
    print(body)


@app.event("app_mention")
async def handle_app_mention_events(body, logger, say):
    try:
        await _handle_app_mention_events(body, logger, say)
    except Exception:
        traceback.print_exc()
        await send_message(say, text="I'm a little over capacity right now. Please try again in a few minutes! :sleeping-hog:")

async def _handle_app_mention_events(body, logger, say):
    logger.info(body)
    print(body)

    user_id = get_user_id(body)
    bot_id = body['authorizations'][0]['user_id']
    event = body["event"]
    thread_ts = event["thread_ts"] if "thread_ts" in event else event["ts"]
    thread = await app.client.conversations_replies(
        channel=event["channel"], ts=thread_ts, limit=CHAT_HISTORY_LIMIT
    )
    if "please summarize this" in event["text"].lower():
        await send_message(say, text="On it!", thread_ts=thread_ts, user_id=user_id, thread=thread)
        summary = summarize_thread(thread)
        await send_message(say, text=summary, thread_ts=thread_ts, user_id=user_id, thread=thread)
        return
    
    thread = preprocess_slack_thread(bot_id, thread)

    first_relevant_message = thread[0]["content"]
    # Disabling this for launch because it can be confusing and jarring when these are incorrect
    # use_feature_flag_prompt = await classify_question(first_relevant_message)
    use_feature_flag_prompt = False
    if use_feature_flag_prompt:
        print("using feature flag prompt for ", first_relevant_message)
        response = await get_query_response(first_relevant_message, thread[1:])
        await send_message(say, text=response, thread_ts=thread_ts, user_id=user_id, thread=thread)
        return
    
    response = await ai_chat_thread(thread)
    await send_message(say, text=response, thread_ts=thread_ts, user_id=user_id, thread=thread)


async def send_message(say, text, thread_ts=None, user_id=None, thread=None):
    posthog.capture("max", "message generated", {"message": text, "thread_ts": thread_ts, "sender": user_id, "context": thread})
    if thread_ts:
        await say(text=text, thread_ts=thread_ts)
    else:
        await say(text)

def get_user_id(body):
    return body.get("event", {}).get("user", None)

# Start your app
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
