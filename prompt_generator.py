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
async def translate_to_flux_prompt(system_prompt: str, user_prompt: str, model: str = "grok-3-mini-latest") -> Optional[str]:
    
    print("프롬프트 생성 중입니다.")
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        translated_text = result["choices"][0]["message"]["content"]
                        
                        print("프롬프트가 생성 되었습니다.")
                        return translated_text
                    else:
                        error_text = await response.text()
                        print(f"API 호출 실패: {response.status}, {error_text}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)  # 재시도 전 잠시 대기 
                        else:
                            return None
        except Exception as e:
            print(f"프롬프트 생성 중 오류 발생: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # 재시도 전 잠시 대기
            else:
                return None
    return None