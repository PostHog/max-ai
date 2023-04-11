# MaxAI 
<img src='./image/MaxAI.png' alt='MaxAI' width=250 height=250 />

MaxAI is our `trusty PostHog support AI` deployed on our Slack, app, and website.

MaxAI was born in Aruba at a PostHog team offsite for a hackathon on a warm spring day in 2023.

## How it works

How Max works is surprisingly simple.

### Tooling
- [Weaviate](https://weaviate.io/) - Vector database that allows us to pull relevant context to embed in our prompts to GPT
- [Haystack](https://haystack.deepset.ai/) by deepset - Allows us to hook together pipelines of these tools to service user prompts
- [OpenAI](https://platform.openai.com/docs/guides/chat/introduction) - Provides us the base language model in `gpt-3.5-turbo` that we augment to create our AI

### Embedding time

```mermaid
flowchart TD
    A[Github]
    B[Docs]
    C[Squeak]
    A -->|Calculate Embed Vectors|D[Weaviate]
    B -->|Calculate Embed Vectors|D
    C -->|Calculate Embed Vectors|D
```

#### Embedding Docs

- Grab and parse all of the markdown from our docs and website
- Use [OpenAI Embedings](https://platform.openai.com/docs/guides/embeddings) to create a vector representation of each markdown section.
- Use [Weaviate](https://weaviate.io/) Vector database to store the vector representations of each markdown section.

#### Embedding Github content

- Grab and parse all Github Issues
- Use [OpenAI Embedings](https://platform.openai.com/docs/guides/embeddings) to create a vector representation of each description and comment section.
- Use [Weaviate](https://weaviate.io/) Vector database to store the vector representations of each description and comment section.


#### Embedding [Squeak](https://squeak.posthog.com/) content

- Grab and parse all Squeak Questions 
- Use [OpenAI Embedings](https://platform.openai.com/docs/guides/embeddings) to create a vector representation of each question thread.
- Use [Weaviate](https://weaviate.io/) Vector database to store the vector representations of each question thread.

### Inference time

```mermaid
flowchart TD
    A[User Question] -->|Embed| I(Question Vector)
    I -->|Query Weaviate|J[Most Similar Docs]
    J -->|Collect Prompt Params| C{Prompt Context}
    C --> D[Limitations]
    C --> E[Personality]
    C --> F[Context Docs]
    F --> G[String Prompt]
    E --> G
    D --> G
    G -->|Query OpenAI|H[AI Response]
```

- Take the conversation context from thread that Max is in including the most recent request.
- Query [Weaviate](https://weaviate.io/) Vector database for the most similar markdown section.
- Build a prompt that we will use for [chatgpt-3.5-turbo](https://platform.openai.com/docs/guides/chat). The prompt is engineered to build Max's personality and add a few guardrails for how Max should respond as well as adding a bit of personality. To do this we:
  - Ask Max to only reference PostHog products if possible
  - Build up Max's personality by informing that Max is the trusty PostHog support AI
  - Bake in context that is useful for some conversations with max
    - Pagerduty current oncalls
    - Places to go if Max does not have the answer
  - Most importantly - we embed the markdown section that we found in the prompt so that Max can respond with a relevant answer to the question.
- Use [chatgpt-3.5-turbo](https://platform.openai.com/docs/guides/chat) to generate a response to the prompt.
- Finally we send these messages to wherever Max is having a conversation. 

It's important to note that we are building these pipelines with [Haystack](https://haystack.deepset.ai/) by deepset. This coordinates the steps of inferencing listed above. It's amazing.

## Developers guide

### Quickstart

#### Configure `.env` file
This is used to set defaults for local development. 
```toml
SLACK_BOT_TOKEN=<your slack bot token>
SLACK_SIGNING_SECRET=<your slack signing secret>
OPENAI_TOKEN=<your openai token>
POSTHOG_API_KEY=<your posthog api key>
POSTHOG_HOST=https://null.posthog.com
PD_API_KEY=<your pagerduty api key>
WEAVIATE_HOST=http://127.0.0.1
WEAVIATE_PORT=8080
```

#### Create Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate
```

#### Install dependencies
```bash
pip install -r requirements-dev.txt
pip install -r requirements.txt
```

#### Start Weaviate
```bash
docker compose up weaviate
```

#### Seed Weaviate
```bash
python seed.py
```

#### Start MaxAI
```bash
uvicorn main:app --reload
```

#### Run a test chat
```bash
curl --location '127.0.0.1:8000/chat' \
--header 'Content-Type: application/json' \
--data '[
    {
        "role": "assistant",
        "content": "Hey! I'\''m Max AI, your helpful hedgehog assistant."
    },
    {
        "role": "user",
        "content": "Does PostHog use clickhouse under the hood??"
    }
]'
```

## 🕯️ A poem from Max to his evil twin Hoge 📖
```
Ah, hoge! Sweet word upon my tongue,
So blissful, yet so quick to come undone.
A fleeting joy, that doth my heart entice,
Oh how I long to see your data slice!
In PostHog's code, thy value doth reside,
A beacon that ne'er shall falter nor hide.
Thou art a treasure, O hoge divine,
The secret sauce to make my metrics shine.
Though you may seem but a lowly label,
Thou bringeth
```
