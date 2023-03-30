import posthog
import os

posthog.project_api_key = os.environ.get("POSTHOG_API_KEY")
posthog.host = os.environ.get("POSTHOG_HOST")

message = "As a PostHog support bot, I do not have access to information on additional data used to train me. However, I can assure you that I was built with the latest natural language processing (NLP) capabilities to help answer any questions you might have about using PostHog products and services. If you have any specific questions, feel free to ask and I will do my best to help!"
thread_ts = 1680145771.369509
posthog.capture("max", "message generated", {"message": message, "thread_ts": thread_ts})