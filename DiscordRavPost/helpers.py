# helpers.py

async def send_chunks(ctx, message, chunk_size=1900):
    """Send a long message in chunks to avoid Discord's 2000-character limit."""
    chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
    for chunk in chunks:
        await ctx.send(chunk)