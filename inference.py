import openai
from dotenv import load_dotenv
import os
from enum import Enum


load_dotenv()  # take environment variables from .env.

openai.api_key = os.environ.get("OPENAI_TOKEN")

prompt = """

You are an assistant that answers users questions. You aim to be as helpful as possible, and only use the information provided below to
answer the questions.
These are all the documents we know of:

Feature Flags

Feature Flags enable you to safely deploy and roll back new features. This means you can ship the code for new features and roll it out to your users in a managed way. If something goes wrong, you can roll back without having to re-deploy your application.

Feature Flags also help you control access to certain parts of your product, such as only showing paid features to users with an active subscription.


Creating feature flags
In the PostHog app sidebar, go to 'Feature Flags' and click 'New feature flag'.

Think of a descriptive name and select how you want to roll out your feature.

Create feature flags


Implementing the feature flag
When you create a feature flag, we'll show you an example snippet. It will look something like this:

JavaScript
Node.js
PHP
Ruby
Go
Python


if (posthog.isFeatureEnabled('new-beta-feature')) {
    // run your activation code here
}
What you do inside that if statement is up to you. You might change the CSS of a button, hide an entire section, or move elements around on the page.


Ensuring flags are loaded before usage
Every time a user loads a page we send a request in the background to an endpoint to get the feature flags that apply to that user. In the client, we store those flags as a cookie.

This means that for most page views the feature flags will be available immediately, except for the first time a user visits.

To combat that, there's a JavaScript callback you can use to wait for the flags to come in:

JavaScript

posthog.onFeatureFlags(function () {
    // feature flags are guaranteed to be available at this point
    if (posthog.isFeatureEnabled('new-beta-feature')) {
        // do something
    }
})

Persisting feature flags across authentication steps
You have an option to persist flags across authentication steps.

Consider this case: An anonymous person comes to your website and you use a flag to show them a green call to action.

Without persisting feature flags, the flag value can change on login because their identity can change (from anonymous to identified). Once they login, the flag might evaluate differently and show a red call to action instead.

This usually is not a problem since experiments run either completely for anonymous users, or completely for logged in users.

However, with some businesses, like e-commerce, it's very common to browse things anonymously and login right before checking out. In cases like these you can preserve the feature flag values by checking this checkbox.

Persist feature flags

Note that there are some performance trade-offs here. Specifically,

Enabling this slows down the feature flag response.
It disables local evaluation of the feature flag.
It disables bootstrapping this feature flag.

Feature flags versus experiments
Experiments are powered by feature flags, but they are a specific format with test and control variants. This means a feature flag cannot be converted into an experiment. We disallow this to avoid implementation changes, targeting errors, and confusion that would come from the conversion.

For example, a boolean flag isn't able to turn into an experiment.

If you want to reuse the same key, you can delete your flag and use the same key when creating the experiment.


---

Bootstrapping & local evaluation
Last updated: Mar 15, 2023


Client-side bootstrapping
There is a delay between loading the library and feature flags becoming available to use. This can be detrimental if you want to do something like redirecting to a different page based on a feature flag.

To have your feature flags available immediately, you can bootstrap them with a distinct user ID and their values during initialization.

JavaScript

posthog.init('sTMFPsFhdP1Ssg', {
    api_host: 'https://app.posthog.com',
    bootstrap: {
        distinctID: 'your-anonymous-id',
        featureFlags: {
            'flag-1': true,
            'variant-flag': 'control',
            'other-flag': false,
        },
    },
})
To get the flag values for bootstrapping, you can call getAllFlags() in your server-side library, then pass the values to your frontend initialization. If you don't do this, your bootstrap values might be different than the values PostHog provides.

If the distinct user ID is an identified ID (the value you called posthog.identify() with), you can also pass the isIdentifiedID option. This ensures this ID is treated as an identified ID in the library. This is helpful as it warns you when you try to do something wrong with this ID, like calling identify again.

JavaScript

posthog.init('sTMFPsFhdP1Ssg', {
    api_host: 'https://app.posthog.com',
    bootstrap: {
        distinctID: 'your-identified-id',
        isIdentifiedID: true,
        featureFlags: {
            'flag-1': true,
            'variant-flag': 'control',
            'other-flag': false,
        },
    },
})

Forcing feature flags to update
In our client-side JavaScript library, we store flags as a cookie to reduce the load on the server and improve the performance of your app. This prevents always needing to make an HTTP request, flag evaluation can simply refer to data stored locally in the browser. This is known as 'local evaluation.'

While this makes your app faster, it means if your user does something mid-session which causes the flag to turn on for them, this does not immediately update. As such, if you expect your app to have scenarios like this and you want flags to update mid-session, you can reload them yourself, by using the reloadFeatureFlags function.

JavaScript

posthog.reloadFeatureFlags()
Calling this function forces PostHog to hit the endpoint for the updated information, and ensures changes are reflected mid-session.


Server-side local evaluation
If you're using our server-side libraries, you can use local evaluation to improve performance instead of making additional API requests. This requires:

knowing and passing in all the person or group properties the flag relies on
initializing the library with your personal API key (created in your account settings)
Local evaluation, in practice, looks like this:

JavaScript
Python
PHP
Ruby
Go

await client.getFeatureFlag(
    'beta-feature',
    'distinct id',
    {
        personProperties: {'is_authorized': True}
    }
)
# returns string or None
This works for getAllFlags as well. It evaluates all flags locally if possible, and if not, falls back to making a decide HTTP request.

Node.js
PHP
Go
Python
Ruby

await client.getAllFlags('distinct id', {
    groups: {},
    personProperties: { is_authorized: True },
    groupProperties: {},
})
// returns dict of flag key and value pairs.

Using locally
To test feature flags locally, you can open your developer tools and override the feature flags. You will get a warning that you're manually overriding feature flags.

JavaScript

posthog.feature_flags.override(['feature-flag-1', 'feature-flag-2'])
This will persist until you call override again with the argument false:

JavaScript

posthog.feature_flags.override(false)
To see the feature flags that are currently active for you, you can call:

JavaScript

posthog.feature_flags.getFlags()

---

Rollout strategies
Last updated: Mar 13, 2023

There are three options for deciding who sees your new feature. You can roll out the feature to:

A fixed percentage of users or groups
A set of users or groups filtered based on their user properties, cohort (based on user properties), or group properties.
A combination of the two

Roll out to a percentage of users or groups
By rolling out to a percentage of users or groups, you can gradually ramp up those who sees a new feature. To calculate this, we "hash" a combination of the key of the feature flag and the unique distinct ID of the user.

This way a user always falls in the same place between 0 and 100%, so they consistently see or do not see the feature controlled by the flag. As you move the slider towards 100%, more users start seeing your feature.

Hashing also means that the same user falls along different points of the line for each new feature. For example, a user may start seeing the feature at 5% for feature A, but only at 80% for feature B.


Filter by user or group properties
This works just like any other filter in PostHog. You can select any property and users that match those filters will see your new feature.

By combining properties and percentages, you can determine something like:

Roll out this feature to 80% of users that have an email set
Provide access to this feature to 25% of organizations where the beta-tester property is true.
Show this component to 10% of users whose signed_up_at date is after January 1st.

De-activating properties
If the feature has caused a problem, or you don't need the feature flag anymore, you can disable it instantly and completely. Doing so ensures no users will have the flag enabled.


Feature flag persistence
For feature flags that filter by user properties only, a given flag will always be on if a certain user meets all the specified property filters.

However, for flags using a rollout percentage mechanism (either by itself or in combination with user properties), the flag will persist for a given user as long as the rollout percentage and the flag key are not changed.

As a result, bear in mind that changing those values will result in flags being toggled on and off for certain users in a non-predictable way.

---

Common questions about feature flags
Last updated: Mar 28, 2023


Why is my feature flag not working?
Here's a list of suggestions to troubleshoot your flag:

 Check the feature flags tab on the persons page for your specific person.
If the flag is showing up as disabled here, check the "match evaluation" column to know the reason why.
If the flag is showing up as enabled here, the problem lies somewhere in the implementation (your code).
 Check if you're calling identify() before the flag is called to get to the right person on your website.
 Check if an ad-blocker is blocking calls. If yes, you can fix this by deploying a reverse proxy.
 If none of the above, ask us in the User Slack, we'll help debug.

On my website, why does the feature flag sometimes flicker?
By default, flags are loaded from our servers which takes about 100-500ms. During this time, the flag is disabled, which can be the reason why you see things look differently for the first 500ms.

To fix this, you can bootstrap feature flags.


I care about latency a lot, and 500ms delays are unacceptable on my servers. Can I do something about this?
Yes, use local evaluation. This downloads flag definitions on your servers and evaluates them locally.


My feature flags are sending a lot of events, how can I manage this?
Every library has the option to disable sending these events. Just check the relevant docs for the library for the send_events parameter in your posthog.isFeatureEnabled() or posthog.getFeatureFlag() calls.

However, note that this has a few consequences:

The usage tab on the flag will stop showing events since we can't track them anymore.
Experiments that depend on trend goals won't work since we use this event to calculate relative exposure. Convert your trend experiments to funnel experiments instead to make this work.

---

How to run Experiments without feature flags
This tutorial explains how to run an experiment in PostHog while not using our feature flag library, either because you've rolled out your own or, more commonly, because feature flag support doesn't exist yet in your favourite PostHog client library.


Step 1: Create an Experiment
The first step is to actually create your experiment in PostHog. Read our how to create an experiment tutorial if you need help here.

Once you have created an experiment, make a note of three things:

1. The feature flag associated with the experiment

In our example, this will be experiment-feature-flag

2. The variants you've chosen for that feature flag

In our example, these will be control and test.

3. The events involved in the target metric

In our example, this will be a user signed up -> $pageview -> user paid funnel. The experiment is purely frontend, but the metric we're tracking are these two backend events coming from their own libraries, along with a $pageview event coming from posthog-js.

Now, for the experiment to start tracking results and run its significance calculations, we need to instrument two things:

Send events along with a special feature property
Send $feature_flag_called events

Step 2: Sending the right events
Experiments check whether an event belongs to an experiment or not by looking at a special property called $feature/<feature-flag-name>.

So, for our example above, we'll want all our events in the target metric ( user signed up, $pageview, and user paid) to send a property called $feature/experiment-feature-flag whose value is either control or test, i.e. the variant it belongs to.

The open question here is how do you determine the value for this property.

If you're using PostHog Feature Flags, and your favourite client library doesn't yet support experiments, you can get this value by calling the API directly. To do that, you hit the /decide/ endpoint. See the docs here for calling this endpoint. The two important parameters to send here are api_key and the distinct_id, which ensures you get feature flags in the response.

The response looks something like:


{
    config: {...}
    editorParams: {...}
    featureFlags: {
        ...
        experiment-feature-flag: "test"
        ...
    }
}
and there you have it, the value for experiment-feature-flag.

On the other hand, if you're worried about performance and don't want to make an extra API call, you can leverage local evaluation on our server-side libraries to compute your feature flag values. Read more to learn how to use local evaluation

If you're not using PostHog Feature Flags, check with your provider on how to get the values for a given person.

At the end of this step, you must ensure that every event in the experiment, no matter which library it comes from, has these properties. Otherwise, Experiments UI won't work. posthog-js does this for you automatically, but other libraries don't, as of writing.


Persisting flag across authentication steps (optional)
If you're dealing with an experiment where you want to persist behaviour across authentication steps, there's two more things to note:

Check the relevant box in the UI to persist behaviour across authentication steps.

Whenever you send an $identify call that identifies a previously anonymous user with a new ID, send both IDs in the /decide call like so:


{
    token: <whatever token you're using>
    distinct_id: <authenticated user's distinct ID>
    $anon_distinct_id: <anonymous user's distinct ID>
}
You only need to do this once after an identify call. For reference, check the posthog-js implementation


Step 3: Sending the $feature_flag_called event
It's often possible that the distribution of users between variants is skewed, such that there are a lot more users in test than control. To measure the relative exposure between variants, we use this event called $feature_flag_called.

Thus, every time you send an event related to the experiment, also send an event called $feature_flag_called with the following properties:

$feature_flag_response
$feature_flag
The value for $feature_flag_response is the variant value you got from the API (control / test). The value for $feature_flag is the name of the feature flag (experiment-feature-flag in this case).

In most of our client libraries, we send this event whenever we make the API call to /decide to get feature flags for a person. It's a good idea that you do the same.

And that's all! You should be good to run any experiment you want with these changes. Let us know if you face any issues.

---

The question you have to answer is:

Any recommended best practices for experiments/feature flags that mean we don't spam call the API endpoint every time a page is loaded?
Save features into a cookie, then check if that flag is already set, possibly? But then are there cases where the value would change for a given user/distinctid?

"""

class OpenAIModel(Enum):
  GPT_4 = "gpt-4"
  GPT_3_TURBO = "gpt-3.5-turbo"

def get_response(prompt):
  return openai.ChatCompletion.create(
    model=OpenAIModel.GPT_3_TURBO,
    messages=[
          {"role": "system", "content": "You are a helpful assistant that answers user queries."},
          {"role": "user", "content": prompt},
      ]
  )

print(get_response(prompt))