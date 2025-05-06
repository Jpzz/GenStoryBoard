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
    await setup_slash_commands()
    await client.tree.sync()
    print('슬래시 명령어가 동기화되었습니다!')
    print('------')
#-------------------------------------------------------------------------------------------------------------#
# 봇 준비 완료 이벤트
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


async def setup_slash_commands():
    print("슬래시 명령어 설정 시작")

    #-------------------------------------------------------------------------------------------------------------#
    # T2I 프롬프트 작성
    #-------------------------------------------------------------------------------------------------------------#
    @client.tree.command(name="c-prompt-t2i", description="ComfyUI 이미지 생성 (텍스트 -> 이미지)")
    @discord.app_commands.choices(model=[
        discord.app_commands.Choice(name="✨FLUX1.0-HIGH✨", value="FLUX1.0-dev"),
        discord.app_commands.Choice(name="⚡FLUX1.0-FAST⚡", value="FLUX1.0-schnell")])
    @discord.app_commands.choices(ratio=[
        discord.app_commands.Choice(name=key, value=key)
        for key, value in json.loads(open(os.path.join(os.path.dirname(__file__),'_comfyui_info', 'output_ratio.json'), 'r').read()).items()])
    @discord.app_commands.describe(model="모델을 선택하세요", positive="긍정적 프롬프트를 입력하세요", ratio="출력 이미지 크기 비율을 입력하세요", seed="랜덤 시드 값 (비워두면 랜덤 생성)")
    async def cPromptT2I(interaction, model: discord.app_commands.Choice[str], positive: str, ratio: discord.app_commands.Choice[str], seed: int = None):
        await interaction.response.defer(ephemeral=True)
        await gf.t2i_process_generate_command(interaction, model, positive, ratio, seed)
    #-------------------------------------------------------------------------------------------------------------#
    # T2I 프롬프트 작성
    #-------------------------------------------------------------------------------------------------------------#

    #-------------------------------------------------------------------------------------------------------------#
    # I2I 프롬프트 작성
    #-------------------------------------------------------------------------------------------------------------#
    @client.tree.command(name="c-prompt-i2i", description="ComfyUI 이미지 생성 (이미지 -> 이미지)")
    @discord.app_commands.choices(model=[
        discord.app_commands.Choice(name="✨FLUX1.0-HIGH✨", value="FLUX1.0-dev"),
        discord.app_commands.Choice(name="⚡FLUX1.0-FAST⚡", value="FLUX1.0-schnell")])
    @discord.app_commands.describe(model="모델을 선택하세요", positive="긍정적 프롬프트를 입력하세요", ref="변환할 원본 이미지를 첨부하세요", ref_weight="원본 이미지 참조 가중치 (0-1 사이 값, 0: 원본 유지, 1: 크게 변형)", seed="랜덤 시드 값 (비워두면 랜덤 생성)")
    async def cPromptI2I(
        interaction, 
        model: discord.app_commands.Choice[str],
        positive: str, 
        ref: discord.Attachment,
        ref_weight: float,
        seed: int = None):
        await interaction.response.defer(ephemeral=True)
        await gf.i2i_process_generate_command(interaction, model, positive, ref, ref_weight, seed)
    #-------------------------------------------------------------------------------------------------------------#
    # I2I 프롬프트 작성
    #-------------------------------------------------------------------------------------------------------------#
    #-------------------------------------------------------------------------------------------------------------#
    # 캐릭터 생성
    #-------------------------------------------------------------------------------------------------------------#
    @client.tree.command(name="c-character-maker", description="사실적인 캐릭터 생성")
    @discord.app_commands.describe(
        shot="샷을 선택하세요",
        gender="캐릭터 성별을 선택하세요",
        age="캐릭터 나이를 선택하세요",
        nationality="캐릭터 국적을 선택하세요",
        body_type="캐릭터 체형을 선택하세요",
        hair_color="캐릭터 머리 색깔을 선택하세요",
        hair_length="캐릭터 머리 길이를 선택하세요",
        face_shape="캐릭터 얼굴 모양을 선택하세요")
    @discord.app_commands.choices(shot=[
        discord.app_commands.Choice(name="head and shoulders portrait", value="Head and shoulders portrait"),
        discord.app_commands.Choice(name="close-up", value="Close-up"),
        discord.app_commands.Choice(name="full body", value="Full body"),
        discord.app_commands.Choice(name="head portrait", value="Head portrait"),
        discord.app_commands.Choice(name="face", value="Face"),
        discord.app_commands.Choice(name="random 🎲", value="random 🎲"),])
    @discord.app_commands.choices(gender=[
        discord.app_commands.Choice(name="man", value="Man"),
        discord.app_commands.Choice(name="woman", value="Woman"),
        discord.app_commands.Choice(name="random 🎲", value="random 🎲"),])
    @discord.app_commands.choices(age=[
        discord.app_commands.Choice(name="early 20s", value="early 20s"),
        discord.app_commands.Choice(name="late 20s", value="late 20s"),
        discord.app_commands.Choice(name="30s", value="30s"),
        discord.app_commands.Choice(name="40s", value="40s"),
        discord.app_commands.Choice(name="50s", value="50s"),
        discord.app_commands.Choice(name="60s", value="60s"),
        discord.app_commands.Choice(name="senior(70+)", value="senior"),
        discord.app_commands.Choice(name="random 🎲", value="random 🎲"),])
    @discord.app_commands.choices(nationality=[
        discord.app_commands.Choice(name="british", value="British"),
        discord.app_commands.Choice(name="american", value="American"),
        discord.app_commands.Choice(name="french", value="French"),
        discord.app_commands.Choice(name="german", value="German"),
        discord.app_commands.Choice(name="italian", value="Italian"),
        discord.app_commands.Choice(name="spanish", value="Spanish"),
        discord.app_commands.Choice(name="korean", value="Korean"),
        discord.app_commands.Choice(name="japanese", value="Japanese"),
        discord.app_commands.Choice(name="chinese", value="Chinese"),
        discord.app_commands.Choice(name="indian", value="Indian"),
        discord.app_commands.Choice(name="russian", value="Russian"),
        discord.app_commands.Choice(name="random 🎲", value="random 🎲"),])
    @discord.app_commands.choices(body_type=[
        discord.app_commands.Choice(name="large", value="Large"),
        discord.app_commands.Choice(name="slight", value="Slight"),
        discord.app_commands.Choice(name="fat", value="Fat"),
        discord.app_commands.Choice(name="skinny", value="Skinny"),
        discord.app_commands.Choice(name="tall", value="Tall"),
        discord.app_commands.Choice(name="short", value="Short"),
        discord.app_commands.Choice(name="random 🎲", value="random 🎲"),])
    @discord.app_commands.choices(hair_color=[
        discord.app_commands.Choice(name="black", value="Black"),
        discord.app_commands.Choice(name="blonde", value="Blonde"),
        discord.app_commands.Choice(name="burgundy", value="Burgundy"),
        discord.app_commands.Choice(name="gray", value="Gray"),
        discord.app_commands.Choice(name="silver", value="Silver"),
        discord.app_commands.Choice(name="random 🎲", value="random 🎲"),])
    @discord.app_commands.choices(hair_length=[
        discord.app_commands.Choice(name="long", value="Long"),
        discord.app_commands.Choice(name="short", value="Short"),
        discord.app_commands.Choice(name="medium", value="Medium"),
        discord.app_commands.Choice(name="random 🎲", value="random 🎲"),])
    @discord.app_commands.choices(face_shape=[
        discord.app_commands.Choice(name="heart", value="Heart"),
        discord.app_commands.Choice(name="v-shape", value="Heart with V-Shape Chin"),
        discord.app_commands.Choice(name="round", value="Round"),
        discord.app_commands.Choice(name="square", value="Square"),
        discord.app_commands.Choice(name="long", value="Long"),
        discord.app_commands.Choice(name="random 🎲", value="random 🎲"),])  
    async def cCharacter(interaction, shot: discord.app_commands.Choice[str], gender: discord.app_commands.Choice[str], age: discord.app_commands.Choice[str], nationality: discord.app_commands.Choice[str], body_type: discord.app_commands.Choice[str], hair_color: discord.app_commands.Choice[str], hair_length: discord.app_commands.Choice[str], face_shape: discord.app_commands.Choice[str], seed: int = None):
        await interaction.response.defer(ephemeral=True)
        await gf.character_1st_process_generate_command(interaction, shot, gender, age, nationality, body_type, hair_color, hair_length, face_shape, seed)
    #-------------------------------------------------------------------------------------------------------------#
    # 캐릭터 생성
    #-------------------------------------------------------------------------------------------------------------#
    
    #-------------------------------------------------------------------------------------------------------------#
    # 캐릭터 T 포즈 생성
    #-------------------------------------------------------------------------------------------------------------#
    @client.tree.command(name="c-t-pose-maker", description="캐릭터 T 포즈 생성")
    @discord.app_commands.describe(
        positive_wearing="착용하려는 옷을 입력하세요",
        positive_body_type = "체형을 입력하세요",
        positive_hair = "머리 스타일을 입력하세요",
        ref="캐릭터 얼굴을 업로드하세요")
    @discord.app_commands.choices(positive_body_type=[
        discord.app_commands.Choice(name="slim", value="slim body"),
        discord.app_commands.Choice(name="normal", value="normal body"),
        discord.app_commands.Choice(name="fat", value="fat body")])
    @discord.app_commands.choices(positive_hair=[
        discord.app_commands.Choice(name="long", value="long hair"),
        discord.app_commands.Choice(name="medium", value="medium hair"),
        discord.app_commands.Choice(name="short", value="short hair")])
    async def cCharacterT(interaction,
                          positive_body_type: discord.app_commands.Choice[str],
                          positive_hair: discord.app_commands.Choice[str],
                          positive_wearing:str,
                          positive_shoes:str,
                          ref: discord.Attachment,
                          anime_style:bool = False):
        await interaction.response.defer(ephemeral=True)
        await gf.character_t_pose_process_generate_command(interaction, positive_body_type, positive_hair, positive_wearing, positive_shoes, ref, anime_style)
    #-------------------------------------------------------------------------------------------------------------#
    # 캐릭터 T 포즈 생성
    #-------------------------------------------------------------------------------------------------------------#

    #-------------------------------------------------------------------------------------------------------------#
    # 애니메이션 캐릭터 생성
    #-------------------------------------------------------------------------------------------------------------#
    @client.tree.command(name="c-anime-maker", description="애니메이션 캐릭터 생성")
    @discord.app_commands.describe(ref="캐릭터 얼굴을 업로드하세요.")
    async def cAnimeCharacter(interaction, ref:discord.Attachment, seed:int = None):
        await interaction.response.defer(ephemeral=True)
        await gf.anime_character_process_generate_command(interaction, ref, seed)
    #-------------------------------------------------------------------------------------------------------------#
    # 애니메이션 캐릭터 생성
    #-------------------------------------------------------------------------------------------------------------#

    #-------------------------------------------------------------------------------------------------------------#
    # 멀티뷰 생성
    #-------------------------------------------------------------------------------------------------------------#
    @client.tree.command(name="c-multiview-maker", description="멀티뷰 캐릭터 생성")
    @discord.app_commands.describe(ref="캐릭터 얼굴을 업로드하세요.")
    async def cMultiView(interaction, ref:discord.Attachment, anime_style:bool = False):
        await interaction.response.defer(ephemeral=True)
        await gf.multiview_character_1st_process_generate_command(interaction, ref, anime_style)
    #-------------------------------------------------------------------------------------------------------------#
    # 멀티뷰 생성
    #-------------------------------------------------------------------------------------------------------------#

    #-------------------------------------------------------------------------------------------------------------#
    # 스토리보드 프롬프트 생성
    #-------------------------------------------------------------------------------------------------------------#
    @client.tree.command(name="c-storyboard-prompt-maker", description="스토리보드 프롬프트 생성")
    @discord.app_commands.describe(ref="포맷에 맞는 콘티를 입력하세요.")
    async def cStoryboardPrompt(interaction, ref:discord.Attachment):
        await interaction.response.defer(ephemeral=True)
        await gf.storyboard_prompt_generate_command(interaction, ref)

    @client.tree.command(name="c-storyboard-maker", description="스토리보드 생성")
    @discord.app_commands.describe(ref="스토리보드 프롬프트 생성을 통해 나온 결과물을 업로드하세요.")
    async def cStoryboardMaker(interaction, ref:discord.Attachment):
        await interaction.response.defer(ephemeral=True)
        await gf.storyboard_process_generate_command(interaction, ref)
    
    #-------------------------------------------------------------------------------------------------------------#
    # 스토리보드 프롬프트 생성
    #-------------------------------------------------------------------------------------------------------------# 
#-------------------------------------------------------------------------------------------------------------#
# 메인 실행
#-------------------------------------------------------------------------------------------------------------# 
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)