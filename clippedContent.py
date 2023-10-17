import requests
from bs4 import BeautifulSoup
import openai
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get OpenAI API key from environment variable
openai_api_key = os.environ["OPENAI_API_KEY"]
openai.api_key = openai_api_key

# User input for the article URL
url = input("Please enter the article link: ")

# Fetch the content of the provided URL
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")


# Function to trim output to stop sentences being cut off midway
def trim_to_last_sentence(text, max_length):
    # Return the text if it's within the max_length
    if len(text) <= max_length:
        return text
    # Search for the last complete sentence within the max_length
    else:
        for i in reversed(range(max_length)):
            if text[i] in [".", "!", "?"]:
                return text[: i + 1]
        return text[:max_length]  # fallback if no punctuation is found within the limit


# Attempt to find the main content area of the page based on certain keywords
keywords = ["content", "article", "blog", "body", "post", "main"]
section_tag = None
for word in keywords:
    section_tag = soup.find(
        lambda tag: tag.name in ["div", "section"] and word in tag.get("class", "")
    )
    if section_tag:
        break

# Extract paragraphs from found section or from the entire page if section is not found
if section_tag:
    paragraphs = section_tag.find_all("p")
else:
    paragraphs = soup.find_all("p")

# Exit if no content is found on the page
if not paragraphs:
    print("No content found.")
    exit()

# Extract all text from the found <p> tags
article_text = " ".join(
    [para.get_text(separator=" ", strip=True) for para in paragraphs]
)

# Define headers for OpenAI requests
headers = {
    "Authorization": f"Bearer {openai_api_key}",
    "Content-Type": "application/json",
    "User-Agent": "OpenAI Python",
}

# Define and send a request to OpenAI for a Twitter summary
# Create a dictionary with the model, message structure, and token limit
tweet_data = {
    "model": "gpt-3.5-turbo",  # Specify the model to be used
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },  # Initial message to set the model's behavior
        {
            "role": "user",  # The user's request
            "content": f"Please provide a concise summary of the following cybersecurity article in a tweet format:\n\n{article_text}",
        },
    ],
    "max_tokens": 80,  # Limit the response length to 80 tokens
}

# Post the data to OpenAI's API endpoint
tweet_response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers=headers,
    data=json.dumps(tweet_data),
)

# Extract the assistant's response from the API's returned JSON
tweet_output = (
    tweet_response.json()["choices"][0]["message"]["content"]
    .replace("[link]", "")  # Remove any placeholders if present
    .strip()
)

# Truncate or modify the response to fit within Twitter's character limit
tweet_output = trim_to_last_sentence(tweet_output, 280 - len(url) - 1)

print("\nTwitter/Bluesky Post:\n")
print(tweet_output + " \n" + url)

# Define and send a request to OpenAI for a Mastodon summary
# Create a dictionary similar to the Twitter request but with Mastodon relevant instructions and token limit
mastodon_data = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": f"Please provide a summary of the following cybersecurity article suitable for a Mastodon post:\n\n{article_text}",
        },
    ],
    "max_tokens": 150,  # Limit the response to 150 tokens
}

# Post the data to OpenAI's API endpoint
mastodon_response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers=headers,
    data=json.dumps(mastodon_data),
)

# Extract the assistant's response
mastodon_output = (
    mastodon_response.json()["choices"][0]["message"]["content"]
    .replace("[link]", "")
    .strip()
)

# Adjust the response to fit within a typical Mastodon post length
mastodon_output = trim_to_last_sentence(mastodon_output, 500)

print("\nMastodon Post:\n")
print(mastodon_output + " \n" + url)
