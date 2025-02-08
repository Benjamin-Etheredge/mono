# Connect to reddit's API and respond to posts on r/roastme.

import contextlib
import os

import ollama
import praw
import praw.models
import streamlit as st
from reddit.utils import download_image_urls, get_images

OLLAMA_URI = os.environ.get("OLLAMA_URI", "http://ollama.k8s.local")
client_id = os.environ
ollama_client = ollama.Client(host=OLLAMA_URI)
HYBRID_MODEL = os.environ.get("HYBRID_MODEL", "llama3.2-vision:11b")
SUMMARY_MODEL = os.environ.get("SUMMARY_MODEL", "deepseek-r1:7b")
# MODEL = os.environ.get('MODEL', 'deepseek-r1:14b')


# template = """
# Roast the person in the image(s) like a reddit user would.

# Be concise.

# <context>
# {}
# </context>
# """
RAG_TEMPLATE = """### Task:
Respond to the user query using the provided context, incorporating inline citations in the format [source_id] **only when the <source_id> tag is explicitly provided** in the context.

### Guidelines:
- If you don't know the answer, clearly state that.
- If uncertain, ask the user for clarification.
- Respond in the same language as the user's query.
- If the context is unreadable or of poor quality, inform the user and provide the best possible answer.
- If the answer isn't present in the context but you possess the knowledge, explain this to the user and provide the answer using your own understanding.
- **Only include inline citations using [source_id] when a <source_id> tag is explicitly provided in the context.**  
- Do not cite if the <source_id> tag is not provided in the context.  
- Do not use XML tags in your response.
- Ensure citations are concise and directly related to the information provided.

### Example of Citation:
If the user asks about a specific topic and the information is found in "whitepaper.pdf" with a provided <source_id>, the response should include the citation like so:  
* "According to the study, the proposed method increases efficiency by 20% [whitepaper.pdf]."
If no <source_id> is present, the response should omit the citation.

### Output:
Provide a clear and direct response to the user's query, including inline citations in the format [source_id] only when the <source_id> tag is present in the context.

<context>
{}
</context>

<user_query>
Summarize the context.
</user_query>"""  # noqa: E501

SUBMISSION_TEMPLATE = """### Task:
Summarize the reddit submission in the provided context.

### Guidelines:
- If you don't know the answer, clearly state that.
- Respond in the same language as the user's query.
- Do not use XML tags in your response.

### Output:
Provide a clear and direct summary of the reddit submssion in the provided context.

<context>

<source_id>
{source_id}
</source_id>

<title>
{title}
</title>

<url>
{url}
</url>

<score>
{score}
</score>

<num_comments>
{num_comments}
</num_comments>

<created_utc>
{created_utc}
</created_utc>

<subreddit>
{subreddit}
</subreddit>

<selftext>
{selftext}
</selftext>

<is_self>
{is_self}
</is_self>
</context>"""


def describe_submission(submission: praw.models.Submission):
    prompt = SUBMISSION_TEMPLATE.format(
        source_id=submission.id,
        title=submission.title,
        url=submission.url,
        score=submission.score,
        num_comments=submission.num_comments,
        created_utc=submission.created_utc,
        subreddit=submission.subreddit.display_name,
        selftext=submission.selftext,
        is_self=submission.is_self,
    )
    print(prompt)
    image_urls = get_images(submission)
    image_paths = download_image_urls(image_urls)
    # st.write(image_paths)

    # response = ollama_client.chat(
    stream = ollama_client.chat(
        model=HYBRID_MODEL,
        stream=True,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": image_paths[:1],
                # 'image': image_paths[0],
            }
        ],
    )
    # data = response['message']['content']
    # print("Summary: ", data)
    # print("In function type: ", type(data))
    # return data
    for chunk in stream:
        yield chunk["message"]["content"]


def query_ollama(submission_summaries):
    context = ""
    for summary in submission_summaries:
        context += "<source-id>\n" + summary + "\n</source-id>\n"
    prompt = RAG_TEMPLATE.format(context)
    stream = ollama_client.chat(
        model=SUMMARY_MODEL,
        stream=True,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    for chunk in stream:
        yield chunk["message"]["content"]


CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
PASSWORD = os.environ["PASSWORD"]
USER_AGENT = os.environ["USER_AGENT"]
USERNAME = os.environ["USERNAME"]

reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    password=PASSWORD,
    user_agent=USER_AGENT,
    username=USERNAME,
)

st.title("Subreddit Summarizer")
st.write(
    "Simple application to visit inputed subreddits, pull X posts from it, summarize the posts, then summarize the summaries."  # noqa: E501
)
st.write("Built by Ben Etheredge")

subreddit_suggestions = [
    "DIY",
    "askreddit",
    "aww",
    "books",
    "crypto",
    "dataisbeautiful",
    "esports",
    "explainlikeimfive",
    "fitness",
    "food",
    "funny",
    "gaming",
    "health",
    "history",
    "memes",
    "movies",
    "music",
    "news",
    "personalfinance",
    "philosophy",
    "photoshopbattles",
    "programming",
    "recipes",
    "relationships",
    "science",
    "space",
    "sports",
    "technology",
    "travel",
    "worldnews",
]

subreddit_name = st.text_input(
    "Input subreddit to search:",
    value="aww",
    help="Enter the name of a subreddit to search. Examples include: aww, books, crypto, dataisbeautiful, etc.",
)
st.write("Note: use '+' to join subreddits to fetch multiple subreddits. E.g., 'funny+aww'")
limit = st.number_input("Number of posts to fetch: ", min_value=1, max_value=100, value=3)
selected_filter = st.radio("Sort: ", options=["hot", "top", "new", "relevance", "comments"])
if subreddit_name:
    subreddit: praw.models.Subreddit = reddit.subreddit(subreddit_name)
    try:
        sort_func = getattr(subreddit, selected_filter)
        submissions = sort_func(limit=limit)
    except Exception as e:
        st.error(f"Error fetching subreddit: {e}")
        st.stop()

    submission_summaries = []
    for idx, submission in enumerate(submissions):
        st.session_state[f"expander_{idx}"] = True
        expander = st.expander(f"Post: {submission.title}", expanded=st.session_state[f"expander_{idx}"])
        with expander:
            st.markdown(f"**Title:** {submission.title}")
            with contextlib.supress(AttributeError):
                # sometimes author is none
                st.markdown(f"**Author:** {submission.author.name}")
            st.markdown(f"**url:** {submission.url}")
            st.markdown("**Summary**")
            with st.chat_message("ai") as _, st.spinner("Generating summary of submission...") as _:
                submission_description = st.write_stream(describe_submission(submission))
                submission_summaries.append(submission_description)
        st.session_state[f"expander_{idx}"] = False

    # Use description model to summarize the summaries
    st.subheader("Summary of Subreddit Posts:")
    with st.chat_message("ai") as _, st.spinner("Generating response...") as _:
        st.write_stream(query_ollama(submission_summaries))
