"""
title: Example Filter
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 0.1
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Awaitable
import logging
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0, description="Priority level for the filter operations."
        )
        max_retries: int = Field(
            default=3, description="Maximum retries for HTTP requests"
        )
        sm_api_key: str = Field(default="", description="API Key of api gateway")
        sm_base_url: str = Field(
            default="", description="SageMaker AI endpoint base url without trailing /"
        )
        sm_endpoint: str = Field(
            default="/predict", description="SageMaker AI endpoint route, e.g. /predict"
        )

    class UserValves(BaseModel):
        pass

    def __init__(self):
        # Indicates custom file handling logic. This flag helps disengage default routines in favor of custom
        # implementations, informing the WebUI to defer file-related operations to designated methods within this class.
        # Alternatively, you can remove the files directly from the body in from the inlet hook
        # self.file_handler = True

        # Initialize 'valves' with specific configurations. Using 'Valves' instance helps encapsulate settings,
        # which ensures settings are managed cohesively and not confused with operational flags like 'file_handler'.
        self.valves = self.Valves()
        pass

    def _find_image_in_latest_messages(self, messages):
        m_index = len(messages) - 1
        message = messages[m_index]
        if message["role"] == "user" and isinstance(message.get("content"), list):
            t_index = 0
            i_index = 0
            image_count = 0
            for c_index, content in enumerate(message["content"]):
                if content["type"] == "image_url":
                    # only process first image if user upload two image at the same time
                    if image_count == 0:
                        i_index = c_index
                        image_count = image_count + 1
                if content["type"] == "text":
                    t_index = c_index
                    # logger.info(content["image_url"])
            return m_index, t_index, i_index, content["image_url"]["url"]
        return None

    def _remove_base64_header(self, base64_string):
        """Remove the 'data:image/jpeg;base64,' prefix from a base64 string"""
        if "," in base64_string:
            return base64_string.split(",", 1)[1]
        return base64_string  # Return as-is if no prefix is found

    async def _call_lambda(
        self, image: str, event_emitter: Callable[[Any], Awaitable[None]]
    ) -> str:
        await event_emitter(
            {
                "type": "status",
                "data": {
                    "description": "✨Sagemaker processing...",
                    "done": False,
                },
            }
        )

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.valves.sm_api_key,
        }
        body = {"image": self._remove_base64_header(image)}
        base = self.valves.sm_base_url
        endpoint = self.valves.sm_endpoint
        url = f"{base}{endpoint}"

        async with aiohttp.ClientSession() as session:
            for attempt in range(self.valves.max_retries):
                try:
                    async with session.post(
                        url, json=body, headers=headers
                    ) as response:
                        response.raise_for_status()
                        response_data = await response.json()
                        print(f"response_data:{response_data}")
                        result = response_data

                        await event_emitter(
                            {
                                "type": "status",
                                "data": {
                                    "description": "🎉Sagemaker process success. Handover to the LLM...",
                                    "done": True,
                                },
                            }
                        )
                        await event_emitter(
                            {
                                "type": "message",
                                "data": {
                                    "content": f"The raw prediction result is: {str(result)}. \n"
                                },
                            }
                        )

                        return result
                except Exception as e:
                    if attempt == self.valves.max_retries - 1:
                        raise RuntimeError(f"Sagemaker Failed：{e}")

    async def inlet(
        self,
        body: dict,
        __event_emitter__: Callable[[Any], Awaitable[None]],
        __user__: Optional[dict] = None,
    ) -> dict:
        # Modify the request body or validate it before processing by the chat completion API.
        # This function is the pre-processor for the API where various checks on the input can be performed.
        # It can also modify the request before sending it to the API.
        logger.info(f"inlet:{__name__}")
        logger.info(f"inlet:body:{body}")
        logger.info(f"inlet:user:{__user__}")

        messages = body.get("messages", [])
        image_info = self._find_image_in_latest_messages(messages)
        if not image_info:
            return body
        message_index, content_text_index, content_image_index, image = image_info

        try:
            result = await self._call_lambda(image, __event_emitter__)

            original_text = messages[message_index]["content"][content_text_index][
                "text"
            ]
            
            messages[message_index]["content"][content_text_index]["text"] = (
                original_text
                + f"Additionaly, this is an image that has been classified by SageMaker. The result is : {result}. Based on that result, try to dig more details or reasoning."
            )
            body["messages"] = messages
        except Exception as e:
            print(f"Error: {e}")

        return body

    def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        # Modify or analyze the response body after processing by the API.
        # This function is the post-processor for the API, which can be used to modify the response
        # or perform additional checks and analytics.
        print(f"outlet:{__name__}")
        print(f"outlet:body:{body}")
        print(f"outlet:user:{__user__}")

        return body
