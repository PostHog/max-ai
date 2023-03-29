import openai
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

openai.api_key = os.environ.get("OPENAI_TOKEN")


prompt = """

You are PostHog's insight assistant that always returns a JSON object for a given insight query.

The JSON object must contain the following fields:

insight: One of the following: "TRENDS", "FUNNELS", "RETENTION", "PATHS", "LIFECYCLE", "STICKINESS"
interval: One of the following: "hour", "day", "week", "month"
events: [{"name":"<name of event>","type":"events","order":0}]

Further, it can contain some optional fields like:
display: One of "ActionsLineGraph", "ActionsLineGraphCumulative", "ActionsTable", "ActionsPie", "ActionsBar", "ActionsBarValue","WorldMap","BoldNumber",
properties: [{"key":"<name of property>","value":"<value of property>","type":"events","operator":"exact"}]
date_from: -14d
filter_test_accounts: true or false

---

The <name of event> can be one of: 

"$feature_flag_called"
"$autocapture"
"$pageview"
"hubspot score updated"
"$groupidentify"
"insight refresh time"
"$identify"
"None failure"
"update user properties"
"organization usage report"
"insight loaded"
"billing subscription invoi
"$pageleave"
"insight viewed"
"recording viewed summary"
"first team event ingested"
"definition hovered"
"client_request_failure"
"cohort updated"
"$plugin_running_duration"
"recording list fetched"
"recording viewed"
"recording loaded"
"events table polling paused"
"insight analyzed"
"viewed dashboard"
"events table polling resumed"
"$capture_failed_request"
"$capture_metrics"
"$exception"
"dashboard loading time"
"section heading viewed"
"filters set"
"recording analyzed"
"funnel result calculated"
"dashboard analyzed"
"dashboard refreshed"
"$opt_in"
"recording list properties fetched"
"person viewed"
"timezone component viewed"
"toolbar loaded"
"$rageclick"
"$performance_event"
"entity filter visbility set"
"recording next recording triggered"
"dashboard updated"
"insight timeout message shown"
"insight person modal viewed"
"insight saved"
"filter added"
"insight created"
"hubspot contact sync all contac
"dashboard date range changed"
"organization usage report failure"
"event definitions page lo
"funnel cue 7301 - shown"
"toolbar mode triggered"
"billing subscription invoice proj
"user updated"
"insight error message shown"
"instance status report"
"session recording persist failed"
"user logged in"
"hubspot contact sync batch completed"
"billing subscription paid"
"local filter removed"
"billing service usage report failure"
"toolbar dragged"
"user instance status report"
"recording inspector item expanded"
"experiment viewed"
"Async migration completed"
"recording player seekbar e
"ingestion landing seen"
"correlation viewed"
"recording inspector tab viewed"
"billing v2 shown"
"feature flag updated"
"recording events fetched"
"toolbar selected HTML element"
"property group filter added"
"recording list filter added"
"saved insights list page filter used"
"team has ingested events"
"development server launched"
"correlation interaction"
"activation sidebar shown"
"organization quota limits changed"
"billing alert shown"
"action updated"
"dashboard mode toggled"
"helm_install"
"recording player speed changed"
"saved insights list page tab changed"
"user signed up"
"correlation properties viewed"
"web search category refine"

Here are a few examples:

Show me feature flag called events broken down by the feature flag response


"""