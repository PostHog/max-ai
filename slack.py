import os
import logging

import openai

from dotenv import load_dotenv
from slack_bolt import App


load_dotenv()

## Initialize OpenAI
openai.api_key = os.environ.get("OPENAI_TOKEN")
models = [m.id for m in openai.Model.list()['data']]
print(f"Available models: {', '.join(models)}")

## "gpt-4" and "gpt-3.5-turbo" are the two we'll use here

# Initializes your app with your bot token and signing secret
app = App(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
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
              "text": "*Welcome to your _App's Home_* :tada:"
            }
          },
          {
            "type": "divider"
          },
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "This button won't do much for now but you can set up a listener for it using the `actions()` method and passing its unique `action_id`. See an example in the `examples` folder within your Bolt app."
            }
          },
          {
            "type": "actions",
            "elements": [
              {
                "type": "button",
                "text": {
                  "type": "plain_text",
                  "text": "Click me!"
                }
              }
            ]
          }
        ]
      }
    )

  except Exception as e:
    logger.error(f"Error publishing home tab: {e}")


def summarize_thread(thread):
  completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                            messages=[{"role": "user", "content": "Hello world!"}])
  return completion.choices[0].message.content


@app.event("message")
def handle_message_events(body, logger, say):
  logger.info(body)
  event = body["event"]

  if "thread_ts" in event:
    thread_ts = event["thread_ts"]
    thread = app.client.conversations_replies(channel=event["channel"], ts=thread_ts)
    summary = summarize_thread(thread)
    print(summary)
    say(text=summary, thread_ts=thread_ts)

@app.event("app_mention")
def handle_app_mention_events(body, logger, say):
        logger.info(body)
        event = body["event"] 

        thread_ts = event.get("thread_ts", None) or event["ts"]

        say(text="hi there! :wave:", thread_ts=thread_ts)


# Start your app
if __name__ == "__main__":
        app.start(port=int(os.environ.get("PORT", 3000)))

