import discord, json, os, utils
from discord.ext import commands
import generate_function as gf
from image_generators import *
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

#-------------------------------------------------------------------------------------------------------------#
# 디스코드 이니셜라이즈
#-------------------------------------------------------------------------------------------------------------#
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='!', intents=intents)
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
#-------------------------------------------------------------------------------------------------------------#
# 디스코드 이니셜라이즈
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 봇 준비 완료 이벤트
#-------------------------------------------------------------------------------------------------------------#
@client.event
async def on_ready():
    print(f'{client.user}이(가) 로그인했습니다!')
    print('------')
#-------------------------------------------------------------------------------------------------------------#
# 봇 준비 완료 이벤트
#-------------------------------------------------------------------------------------------------------------#


#-------------------------------------------------------------------------------------------------------------#
# 명령어 처리
#-------------------------------------------------------------------------------------------------------------#
@client.command(name='flux')
async def flux(ctx, *args):
    if not args:
        await ctx.send('사용법: !flux [프롬프트]')
        return
    
    prompt = ' '.join(args)
    await ctx.send(f'프롬프트: {prompt}\n이미지 생성 중...')
    
    try:
        image_url = await gf.generate_flux_image(prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='dalle')
async def dalle(ctx, *args):
    if not args:
        await ctx.send('사용법: !dalle [프롬프트]')
        return
    
    prompt = ' '.join(args)
    await ctx.send(f'프롬프트: {prompt}\n이미지 생성 중...')
    
    try:
        image_url = await gf.generate_dalle_image(prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='sd')
async def stable_diffusion(ctx, *args):
    if not args:
        await ctx.send('사용법: !sd [프롬프트]')
        return
    
    prompt = ' '.join(args)
    await ctx.send(f'프롬프트: {prompt}\n이미지 생성 중...')
    
    try:
        image_url = await gf.generate_stable_diffusion_image(prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='midjourney', aliases=['mj'])
async def midjourney(ctx, *args):
    if not args:
        await ctx.send('사용법: !midjourney [프롬프트] 또는 !mj [프롬프트]')
        return
    
    prompt = ' '.join(args)
    await ctx.send(f'프롬프트: {prompt}\n이미지 생성 중...')
    
    try:
        image_url = await gf.generate_midjourney_image(prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='help')
async def help_command(ctx):
    help_text = '''
    **사용 가능한 명령어:**
    
    **!flux [프롬프트]** - Flux 모델을 사용하여 이미지 생성
    **!dalle [프롬프트]** - DALL-E 모델을 사용하여 이미지 생성
    **!sd [프롬프트]** - Stable Diffusion을 사용하여 이미지 생성
    **!midjourney [프롬프트]** 또는 **!mj [프롬프트]** - Midjourney 스타일 이미지 생성
    **!help** - 이 도움말 표시
    
    **한국어 프롬프트 지원:**
    모든 명령어는 한국어 프롬프트를 영어로 변환하여 처리합니다.
    '''
    await ctx.send(help_text)

#-------------------------------------------------------------------------------------------------------------#
# 명령어 처리
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 한국어 프롬프트 처리
#-------------------------------------------------------------------------------------------------------------#
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # 명령어 처리를 위해 process_commands 호출
    await client.process_commands(message)
    
    # 명령어가 아닌 일반 메시지 처리
    if not message.content.startswith('!'):
        return
    
    # 한국어 프롬프트 처리 로직은 여기에 추가
#-------------------------------------------------------------------------------------------------------------#
# 한국어 프롬프트 처리
#-------------------------------------------------------------------------------------------------------------#


#-------------------------------------------------------------------------------------------------------------#
# 이미지 생성 명령어
#-------------------------------------------------------------------------------------------------------------#

@client.command(name='한글')
async def korean_prompt(ctx, *args):
    if not args:
        await ctx.send('사용법: !한글 [한국어 프롬프트]')
        return
    
    korean_text = ' '.join(args)
    await ctx.send(f'한국어 프롬프트: {korean_text}\n번역 및 이미지 생성 중...')
    
    try:
        # 한국어를 영어로 번역
        english_prompt = await gf.translate_korean_to_english(korean_text)
        if not english_prompt:
            await ctx.send('프롬프트 번역에 실패했습니다.')
            return
        
        await ctx.send(f'번역된 프롬프트: {english_prompt}\n이미지 생성 중...')
        
        # 번역된 프롬프트로 이미지 생성
        image_url = await gf.generate_flux_image(english_prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='한글sd')
async def korean_sd(ctx, *args):
    if not args:
        await ctx.send('사용법: !한글sd [한국어 프롬프트]')
        return
    
    korean_text = ' '.join(args)
    await ctx.send(f'한국어 프롬프트: {korean_text}\n번역 및 이미지 생성 중...')
    
    try:
        # 한국어를 영어로 번역
        english_prompt = await gf.translate_korean_to_english(korean_text)
        if not english_prompt:
            await ctx.send('프롬프트 번역에 실패했습니다.')
            return
        
        await ctx.send(f'번역된 프롬프트: {english_prompt}\n이미지 생성 중...')
        
        # 번역된 프롬프트로 이미지 생성
        image_url = await gf.generate_stable_diffusion_image(english_prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='한글mj')
async def korean_mj(ctx, *args):
    if not args:
        await ctx.send('사용법: !한글mj [한국어 프롬프트]')
        return
    
    korean_text = ' '.join(args)
    await ctx.send(f'한국어 프롬프트: {korean_text}\n번역 및 이미지 생성 중...')
    
    try:
        # 한국어를 영어로 번역
        english_prompt = await gf.translate_korean_to_english(korean_text)
        if not english_prompt:
            await ctx.send('프롬프트 번역에 실패했습니다.')
            return
        
        await ctx.send(f'번역된 프롬프트: {english_prompt}\n이미지 생성 중...')
        
        # 번역된 프롬프트로 이미지 생성
        image_url = await gf.generate_midjourney_image(english_prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='한글dalle')
async def korean_dalle(ctx, *args):
    if not args:
        await ctx.send('사용법: !한글dalle [한국어 프롬프트]')
        return
    
    korean_text = ' '.join(args)
    await ctx.send(f'한국어 프롬프트: {korean_text}\n번역 및 이미지 생성 중...')
    
    try:
        # 한국어를 영어로 번역
        english_prompt = await gf.translate_korean_to_english(korean_text)
        if not english_prompt:
            await ctx.send('프롬프트 번역에 실패했습니다.')
            return
        
        await ctx.send(f'번역된 프롬프트: {english_prompt}\n이미지 생성 중...')
        
        # 번역된 프롬프트로 이미지 생성
        image_url = await gf.generate_dalle_image(english_prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

#-------------------------------------------------------------------------------------------------------------#
# 이미지 생성 명령어
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 캐릭터 지정 이미지 생성 명령어
#-------------------------------------------------------------------------------------------------------------#

@client.command(name='캐릭터')
async def character_image(ctx, character=None, *args):
    if not character or not args:
        await ctx.send('사용법: !캐릭터 [캐릭터명] [한국어 프롬프트]')
        return
    
    korean_text = ' '.join(args)
    await ctx.send(f'캐릭터: {character}\n한국어 프롬프트: {korean_text}\n번역 및 이미지 생성 중...')
    
    try:
        # 한국어를 영어로 번역하고 캐릭터 정보 추가
        english_prompt = await gf.translate_korean_to_english_with_character(korean_text, [character])
        if not english_prompt:
            await ctx.send('프롬프트 번역에 실패했습니다.')
            return
        
        await ctx.send(f'번역된 프롬프트: {english_prompt}\n이미지 생성 중...')
        
        # 번역된 프롬프트로 이미지 생성
        image_url = await gf.generate_flux_image(english_prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='캐릭터sd')
async def character_sd(ctx, character=None, *args):
    if not character or not args:
        await ctx.send('사용법: !캐릭터sd [캐릭터명] [한국어 프롬프트]')
        return
    
    korean_text = ' '.join(args)
    await ctx.send(f'캐릭터: {character}\n한국어 프롬프트: {korean_text}\n번역 및 이미지 생성 중...')
    
    try:
        # 한국어를 영어로 번역하고 캐릭터 정보 추가
        english_prompt = await gf.translate_korean_to_english_with_character(korean_text, [character])
        if not english_prompt:
            await ctx.send('프롬프트 번역에 실패했습니다.')
            return
        
        await ctx.send(f'번역된 프롬프트: {english_prompt}\n이미지 생성 중...')
        
        # 번역된 프롬프트로 이미지 생성
        image_url = await gf.generate_stable_diffusion_image(english_prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='캐릭터mj')
async def character_mj(ctx, character=None, *args):
    if not character or not args:
        await ctx.send('사용법: !캐릭터mj [캐릭터명] [한국어 프롬프트]')
        return
    
    korean_text = ' '.join(args)
    await ctx.send(f'캐릭터: {character}\n한국어 프롬프트: {korean_text}\n번역 및 이미지 생성 중...')
    
    try:
        # 한국어를 영어로 번역하고 캐릭터 정보 추가
        english_prompt = await gf.translate_korean_to_english_with_character(korean_text, [character])
        if not english_prompt:
            await ctx.send('프롬프트 번역에 실패했습니다.')
            return
        
        await ctx.send(f'번역된 프롬프트: {english_prompt}\n이미지 생성 중...')
        
        # 번역된 프롬프트로 이미지 생성
        image_url = await gf.generate_midjourney_image(english_prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

@client.command(name='캐릭터dalle')
async def character_dalle(ctx, character=None, *args):
    if not character or not args:
        await ctx.send('사용법: !캐릭터dalle [캐릭터명] [한국어 프롬프트]')
        return
    
    korean_text = ' '.join(args)
    await ctx.send(f'캐릭터: {character}\n한국어 프롬프트: {korean_text}\n번역 및 이미지 생성 중...')
    
    try:
        # 한국어를 영어로 번역하고 캐릭터 정보 추가
        english_prompt = await gf.translate_korean_to_english_with_character(korean_text, [character])
        if not english_prompt:
            await ctx.send('프롬프트 번역에 실패했습니다.')
            return
        
        await ctx.send(f'번역된 프롬프트: {english_prompt}\n이미지 생성 중...')
        
        # 번역된 프롬프트로 이미지 생성
        image_url = await gf.generate_dalle_image(english_prompt)
        if image_url:
            await ctx.send(f'생성된 이미지: {image_url}')
        else:
            await ctx.send('이미지 생성에 실패했습니다.')
    except Exception as e:
        await ctx.send(f'오류 발생: {str(e)}')

#-------------------------------------------------------------------------------------------------------------#
# 캐릭터 지정 이미지 생성 명령어
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 메인 실행
#-------------------------------------------------------------------------------------------------------------# 
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)