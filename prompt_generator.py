import aiohttp
from typing import Optional, List
import asyncio
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Get API key from environment variable for security
XAI_API_KEY = os.environ.get("XAI_API_KEY")

#-------------------------------------------------------------------------------------------------------------#
# 프롬프트 생성
#-------------------------------------------------------------------------------------------------------------# 
async def translate_to_flux_prompt(korean_text: List[str], model: str = "grok-3-mini-latest") -> Optional[str]:
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "anthropic-version": "2023-06-01"
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    translated_text = result["content"][0]["text"]
                    
                    # Add character and sub-character information if provided
                    final_prompt = translated_text
                    
                    if character and character[0]:
                        char_list = ", ".join(character)
                        final_prompt = f"{final_prompt}, {char_list}"
                    
                    if sub_character and sub_character[0]:
                        sub_char_list = ", ".join(sub_character)
                        final_prompt = f"{final_prompt}, with {sub_char_list}"
                    
                    print("프롬프트 생성 완료!")
                    return final_prompt
                else:
                    error_text = await response.text()
                    print(f"API 호출 실패: {response.status}, {error_text}")
                    return None
        except Exception as e:
            print(f"프롬프트 생성 중 오류 발생: {str(e)}")
            return None