from dotenv import load_dotenv
from typing import Dict
from openai import AsyncOpenAI
import os
import asyncio
from aiohttp import ClientSession

load_dotenv("keys.env")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")



class Agent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_KEY)
        self.user_threads: Dict[str, str] = {}  # Maps user_id to thread_id
        self.assistant = None

    async def initialize(self):
        """Initialize the assistant asynchronously"""
        self.assistant = await self.client.beta.assistants.retrieve("asst_8uPkGGtHHg8S5HiEM3FyE3sm")

    async def get_user_thread(self, user_id: str) -> str:
        """Get or create thread for user asynchronously"""
        if user_id not in self.user_threads:
            thread = await self.client.beta.threads.create()
            self.user_threads[user_id] = thread.id
        return self.user_threads[user_id]

    async def send_message(self, user_id: str, message: str) -> str:
        """Send message and get response for specific user asynchronously"""
        if not self.assistant:
            await self.initialize()
            
        thread_id = await self.get_user_thread(user_id)
        
        # Add user's message to thread
        await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )

        # Run assistant
        run = await self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id
        )

        # Wait for completion with async sleep
        while True:
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run.status == 'completed':
                break
            await asyncio.sleep(1)

        # Get latest message
        messages = await self.client.beta.threads.messages.list(thread_id=thread_id)
        return messages.data[0].content[0].text.value