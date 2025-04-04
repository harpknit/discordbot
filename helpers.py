import requests
from bs4 import BeautifulSoup
import logging

designer_by_user = {} 

def get_pattern_title(url, full=False):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string
            raw_title = title.replace(" - Ravelry", "").strip()
            if raw_title.startswith("Ravelry: "):
                raw_title = raw_title.replace("Ravelry: ", "")
            if full:
                raw_title = raw_title.replace("pattern by", "by")
            elif "pattern by" in raw_title:
                raw_title = raw_title.split(" pattern by")[0].strip()
            return raw_title
        else:
            return None
    except Exception as e:
        logging.info("Error fetching title:", e)
        return None
        
async def send_chunks(ctx, message, chunk_size=1900):
    """Send a long message in chunks to avoid Discord's 2000-character limit."""
    chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
    for chunk in chunks:
        await ctx.send(chunk)

