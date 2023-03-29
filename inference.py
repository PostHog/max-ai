import openai
from dotenv import load_dotenv
import os
from enum import Enum


load_dotenv()  # take environment variables from .env.

openai.api_key = os.environ.get("OPENAI_TOKEN")

prompt = """

You are an assistant that answers users questions. You aim to be as helpful as possible, and only use the information provided below to
answer the questions.

If the information is not enough, you can ask the user for more information. You can ask at most 2 questions.

These are all the documents we know of:

Feature Flags

Feature Flags enable you to safely deploy and roll back new features. This means you can ship the code for new features and roll it out to your users in a managed way. If something goes wrong, you can roll back without having to re-deploy your application.

Feature Flags also help you control access to certain parts of your product, such as only showing paid features to users with an active subscription.


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

Feature Flags Posthog-js SDK

Here's how you can use them:

Do something when the feature flags load:

The argument callback(flags: string[]) will be called when the feature flags are loaded.

In case the flags are already loaded, it'll be called immediately. Additionally, it will also be called when the flags are re-loaded e.g. after calling identify or reloadFeatureFlags.

JavaScript

posthog.onFeatureFlags(callback)
Check if a feature is enabled:
JavaScript

posthog.isFeatureEnabled('keyword')
Trigger a reload of the feature flags:
JavaScript

posthog.reloadFeatureFlags()
By default, this function will send a $feature_flag_called event to your instance every time it's called so you're able to do analytics. You can disable this by passing the send_event property:
JavaScript

posthog.isFeatureEnabled('keyword', { send_event: false })

Feature Flag Payloads
Payloads allow you to retrieve a value that is associated with the matched flag. The value can be a string, boolean, number, dictionary, or array. This allows for custom configurations based on values defined in the posthog app.

JavaScript

posthog.getFeatureFlagPayload('keyword')

Bootstrapping Flags
There is a delay between loading the library and feature flags becoming available to use. For some cases, like redirecting users to a different page based on a feature flag, this is extremely detrimental, as the flags load after the redirect logic occurs, thus never working.

In cases like these, where you want flags to be immediately available on page load, you can use the bootstrap library option.

This allows you to pass in a distinctID and feature flags during library initialisation, like so:

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
To compute these flag values, use the corresponding getAllFlags method in your server-side library. Note that bootstrapping flags requires server-side initialisation.

If the ID you're passing in is an identified ID (that is, an ID with which you've called posthog.identify() elsewhere), you can also pass in the isIdentifiedID bootstrap option, which ensures that this ID is treated as an identified ID in the library. This is helpful as it warns you when you try to do something wrong with this ID, like calling identify again.

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
Note: Passing in a distinctID to bootstrap replaces any existing IDs, which means you may fail to connect any old anonymous user events with the logged in person, if your logic calls identify in the frontend immediately on login. In this case, you can omit passing in the distinctID.

---

Feature flags Posthog-node SDK

PostHog's feature flags enable you to safely deploy and roll back new features.

When using them with one of libraries, you should check if a feature flag is enabled and use the result to toggle functionality on and off in you application.

How to check if a flag is enabled

Note: Whenever we face an error computing the flag, the library returns undefined, instead of true, false, or a string variant value.

Node.js

// isFeatureEnabled(key: string, distinctId: string, options: {}): Promise<boolean | undefined>
const isMyFlagEnabledForUser = await client.isFeatureEnabled('flag-key', 'user distinct id')

if (isMyFlagEnabledForUser) {
    // Do something differently for this user
}
Get a flag value

If you're using multivariate feature flags, you can also get the value of the flag, as well as whether or not it is enabled.

Note: Whenever we face an error computing the flag, the library returns None, instead of true or false or a string variant value.

Node.js

// getFeatureFlag(key: string, distinctId: string, options: {}): Promise<string | boolean | undefined>
const flagValue = await client.getFeatureFlag('flag-key', 'user distinct id')
Get a flag payload

Posthog Node v2.3.0 introduces feature flag payloads. Feature flags can be returned with matching payloads which are JSONType (string, number, boolean, dictionary, array) values. This allows for custom configurations based on values defined in the posthog app.

Note: getFeatureFlag does not need to be called prior to getFeatureFlagPayload. getFeatureFlagPayload will implicitly perform getFeatureFlag to determine the matching flag and return the corresponding payload.

Node.js

// getFeatureFlagPayload(key: string, distinctId: string, matchValue?: string | boolean, options: {}): Promise<JsonType | undefined>
const flagPayload = await client.getFeatureFlagPayload('flag-key', 'user distinct id')
Overriding server properties

Sometimes, you might want to evaluate feature flags using properties that haven't been ingested yet, or were set incorrectly earlier. You can do so by setting properties the flag depends on with these calls.

For example, if the beta-feature depends on the is_authorized property, and you know the value of the property, you can tell PostHog to use this property, like so:

Node.js

// getFeatureFlag(
//    key: string,
//    distinctId: string,
//    options?: {
//      groups?: Record<string, string>
//      personProperties?: Record<string, string>
//      groupProperties?: Record<string, Record<string, string>>
//      onlyEvaluateLocally?: boolean
//      sendFeatureFlagEvents?: boolean
//    }
//  ): Promise<string | boolean | undefined>
const flagValue = await client.getFeatureFlag('flag-key', 'user distinct id', {
    personProperties: { is_authorized: true },
})
The same holds for groups. If you have a group named organisation, you can add properties like so:

Node.js

const flagValue = await client.getFeatureFlag('flag-key', 'user distinct id', {groups:{'organisation': 'google'}, groupProperties:{'organisation': {'is_authorized': True}})
Getting all flag values

You can also get all known flag values as well. This is useful when you want to seed a frontend client with initial known flags. Like all methods above, this also takes optional person and group properties, if known.

Node.js

await client.getAllFlags('distinct id', { groups: {}, personProperties: { is_authorized: True }, groupProperties: {} })
// returns dict of flag key and value pairs.

Local Evaluation
Note: To enable local evaluation of feature flags you must also set a personal_api_key when configuring the integration, as described in the Installation section.

Note: This feature requires version 2.0 of the library, which in turn requires a minimum PostHog version of 1.38

All feature flag evaluation requires an API request to your PostHog servers to get a response. However, where latency matters, you can evaluate flags locally. This is much faster, and requires two things to work:

The library must be initialised with a personal API key
You must know all person or group properties the flag depends on.
Then, the flag can be evaluated locally. The method signature looks exactly like above.

Node.js

await client.getFeatureFlag('beta-feature', 'distinct id', { personProperties: { is_authorized: True } })
// returns string or None
Note: New feature flag definitions are polled every 30 seconds by default, which means there will be up to a 30 second delay between you changing the flag definition, and it reflecting on your servers. You can change this default on the client by setting featureFlagsPollingInterval during client initialisation.

This works for getAllFlags as well. It evaluates all flags locally if possible. If even one flag isn't locally evaluable, it falls back to decide.

Node.js

await client.getAllFlags('distinct id', { groups: {}, personProperties: { is_authorized: True }, groupProperties: {} })
// returns dict of flag key and value pairs.
Restricting evaluation to local only

Sometimes, performance might matter to you so much that you never want an HTTP request roundtrip delay when computing flags. In this case, you can set the only_evaluate_locally parameter to true, which tries to compute flags only with the properties it has. If it fails to compute a flag, it returns None, instead of going to PostHog's servers to get the value.

Cohort expansion

To support feature flags that depend on cohorts locally as well, we translate the cohort definition into person properties, so that the person properties you set can be used to evaluate cohorts as well.

However, there are a few constraints here and we don't support doing this for arbitrary cohorts. Cohorts won't be evaluated locally if:

They have non-person properties
There's more than one cohort in the feature flag definition.
The cohort in the feature flag is in the same group as another condition.
The cohort has nested AND-OR filters. Only simple cohorts that have a top level OR group, and inner level ANDs will be evaluated locally.
Note that this restriction is for local evaluation only. If you're hitting PostHog's servers, all of these cohorts will be evaluated as expected. Further, posthog-node v2.6.0 onwards, and posthog-python v2.4.0 onwards do not face this issue and can evaluate all cohorts locally.


Reloading feature flags
When initializing PostHog, you can configure the interval at which feature flags are polled (fetched from the server). However, if you need to force a reload, you can use reloadFeatureFlags:

Node.js

await client.reloadFeatureFlags()

// Do something with feature flags here

---

The question you have to answer is:

"""


prompt_1 = """Any recommended best practices for experiments/feature flags that mean we don't spam call the API endpoint every time a page is loaded? Save features into a cookie, then check if that flag is already set, possibly?
But then are there cases where the value would change for a given user/distinctid?
"""

prompt_2 = """
Hey all, I'm trying to do AB testing on our marketing homepage using posthog. I have JS that updates the actual page.
However, the feature flag isn't loaded early enough. I know the docs mentioned an issue, but I found them confusing. Can anyone help?
"""

prompt_3 = """
My feature flags are not working, how do I fix this?
"""


class OpenAIModel(Enum):
  GPT_4 = "gpt-4"
  GPT_3_TURBO = "gpt-3.5-turbo"


def get_response(question, follow_up_messages=None, model=OpenAIModel.GPT_3_TURBO.value):
  messages = [
    {"role": "system", "content": "You are a helpful assistant that answers user queries."},
    {"role": "user", "content": question},
  ]

  if follow_up_messages:
    messages += follow_up_messages

  api_response = openai.ChatCompletion.create(
    model=model,
    messages=messages
  )

  return api_response["choices"][0]["message"]["content"]

# print(get_response(prompt, prompt_3))
