import utils, discord, os, json, random, requests, threading, time, asyncio
from concurrent.futures import ThreadPoolExecutor
from comfy_editor import *
from image_generators import *
from image_callbacks import *
from file_processors import *
from queue import Queue

#-------------------------------------------------------------------------------------------------------------#
# 생성형 글로벌 파라미터 
#-------------------------------------------------------------------------------------------------------------#
progress_messages = {}
server_list = []
workflow_parameter = {}
workflow_logic = {}
#-------------------------------------------------------------------------------------------------------------#
# 생성형 글로벌 파라미터 
#-------------------------------------------------------------------------------------------------------------#


#-------------------------------------------------------------------------------------------------------------#
# 레디
#-------------------------------------------------------------------------------------------------------------#
def on_ready():
    global server_list
    global workflow_parameter
    global workflow_logic
    server_list = utils.initialize_server_list()
    workflow_parameter = utils.load_workflow_parameter()
    workflow_logic = utils.load_workflow_logic()
#-------------------------------------------------------------------------------------------------------------#
# 레디
#-------------------------------------------------------------------------------------------------------------#


#-------------------------------------------------------------------------------------------------------------#
# 이미지 생성 진행률 업데이트를 위한 함수
#-------------------------------------------------------------------------------------------------------------#
async def update_progress_message(progress_message, progress_value, progress_max):
    """
    디스코드 임베드 메시지의 진행률을 업데이트합니다
    
    Args:
        interaction: 디스코드 인터랙션 객체
        progress_message: 업데이트할 메시지 객체
        progress_value: 현재 진행 값
        progress_max: 최대 진행 값
    """
    # 진행률 계산 및 표시
    percentage = int((progress_value / progress_max) * 100)
    progress_bar = generate_progress_bar(percentage)
    
    # 임베드 생성
    embed = utils.set_embed(
        "이미지 생성 중...",
        f"{progress_bar}\n**진행률**: {progress_value}/{progress_max} ({percentage}%)",
        discord.Color.blue()
    )
    
    # 메시지 업데이트
    try:
        await progress_message.edit(embed=embed)
    except Exception as e:
        print(f"진행률 메시지 업데이트 중 오류: {str(e)}")
#-------------------------------------------------------------------------------------------------------------#
# 이미지 생성 진행률 업데이트를 위한 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 진행 표시줄 생성 함수
#-------------------------------------------------------------------------------------------------------------#
def generate_progress_bar(percentage, length=20):
    """
    텍스트 기반 진행 표시줄을 생성합니다
    
    Args:
        percentage: 진행률 (0-100)
        length: 진행 표시줄 길이
        
    Returns:
        텍스트 진행 표시줄
    """
    filled_length = int(length * percentage / 100)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"[{bar}] {percentage}%"
#-------------------------------------------------------------------------------------------------------------#
# 진행 표시줄 생성 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 서버 설정 확인 함수
#-------------------------------------------------------------------------------------------------------------# 
async def check_server_setting(interaction):
    """
    서버 설정을 확인하고 서버 IP를 반환하는 함수
    
    Args:
        interaction: Discord 상호작용 객체
        
    Returns:
        server_ip 또는 None
    """
    global server_list
    server_ip = None
    server_port = 8000  # ComfyUI 기본 포트
    
    # 서버 리스트가 초기화되지 않았거나 올바른 형식이 아닌 경우 초기화
    if not isinstance(server_list, dict) or 'servers' not in server_list:
        server_list = utils.initialize_server_list()
    
    for server in server_list['servers']:
        if server['name'] == 'vilab-genAI-server4':
            server_ip = server['ip']
            # 서버 정보에 포트가 있는지 확인
            if 'port' in server:
                server_port = server['port']
            print("서버가 확인되었습니다.")        
            break
    
    if server_ip is None:
        failed = utils.set_embed("서버 찾기 실패", "서버 목록에 서버가 존재하지 않습니다.", discord.Color.red())
        await interaction.followup.send(embed=failed, ephemeral=True)
        
    return server_ip
#-------------------------------------------------------------------------------------------------------------#
# 서버 설정 확인 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 워크플로우 파일 로드 함수
#-------------------------------------------------------------------------------------------------------------#
def load_prompt(prompt_workflow):
    """
    워크플로우 파일을 로드하여 프롬프트 데이터 반환
    
    Args:
        prompt_workflow: 워크플로우 파일명
        
    Returns:
        프롬프트 데이터 (JSON)
    """
    prompt_path = os.path.join(os.path.dirname(__file__), '_comfyui_workflows', prompt_workflow)
    with open(prompt_path, "r") as f:
        prompt = json.load(f)
    return prompt
#-------------------------------------------------------------------------------------------------------------#
# 워크플로우 파일 로드 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 워크플로우 결과 이미지 처리 함수
#-------------------------------------------------------------------------------------------------------------#
def process_result_image(result):
    """
    ComfyUI 결과에서 이미지 파일을 처리
    
    Args:
        result: ComfyUI 생성 결과
        
    Returns:
        처리된 이미지 파일 리스트
    """

    print("이미지 처리 시작")
    # 이미지 파일 처리
    image_files = []
    image_paths = {}
    try:
        for node_id, images in result.items():
            for i, img_data in enumerate(images):
                # 바이너리 데이터를 파일로 저장
                img_filename = f"result_{node_id}_{i}.png"
                temp_path = os.path.join(os.path.dirname(__file__), "_temp", img_filename)
                
                # 임시 디렉토리가 없으면 생성
                os.makedirs(os.path.join(os.path.dirname(__file__), "_temp"), exist_ok=True)
                
                # 이미지 데이터 저장
                with open(temp_path, "wb") as img_file:
                    img_file.write(img_data["data"])
                
                # discord.File 객체 생성
                image_files.append(discord.File(temp_path, filename=img_filename))
                image_paths[f"img_{i}"] = temp_path
    except Exception as e:
        print(f"이미지 처리 중 오류: {e}")
    
    return image_files, image_paths
#-------------------------------------------------------------------------------------------------------------#
# 워크플로우 결과 이미지 처리 함수
#-------------------------------------------------------------------------------------------------------------#

def upload_file(temp_file_path, temp_file_name, server_ip, overwrite: bool = True, subfolder: str = 'upload'):
    try:
        # 업로드할 파일 데이터 준비
        with open(temp_file_path, 'rb') as file:
            file_data = file.read()
        
        # 업로드 요청 URL 및 데이터 생성
        url = f"http://{server_ip}:8000/upload/image"
        files = {
            'image': (temp_file_name, file_data, 'image/png'),
            'overwrite': ('overwrite', 'true' if overwrite else 'false')
        }
        
        # 서브폴더 지정
        data = {'subfolder': subfolder}
        
        # 업로드 요청
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            # 응답 확인
            response_data = response.json()
            if "name" in response_data:
                print(f"파일 업로드 성공: {response_data['name']}")
                return response_data["name"]
            else:
                print(f"파일 업로드 응답에 이름이 없습니다: {response_data}")
                return None
        else:
            print(f"파일 업로드 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"파일 업로드 중 오류 발생: {str(e)}")
        return None
    finally:
        # 임시 파일 정리 (선택적)
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass

#-------------------------------------------------------------------------------------------------------------#
# 이미지 업로드 함수
#-------------------------------------------------------------------------------------------------------------# 
async def upload_image(interaction, server_ip, ref, overwrite: bool = True):
    """이미지를 업로드하고 파일 이름을 반환합니다."""    
    temp_file_name = utils.set_file_name(interaction, "png")
    temp_file_path = os.path.join(os.path.dirname(__file__), "_temp", temp_file_name)
    
    try:
        # ref가 discord.Attachment 객체인 경우
        if isinstance(ref, discord.Attachment):
            # 파일 다운로드 및 저장
            await ref.save(temp_file_path)
        # ref가 문자열 경로인 경우 (로컬 파일 경로)
        elif isinstance(ref, str) and os.path.exists(ref):
            # 파일 복사
            import shutil
            shutil.copy2(ref, temp_file_path)
        else:
            raise ValueError("지원되지 않는 참조 유형입니다. discord.Attachment 또는 유효한 파일 경로가 필요합니다.")
            
        # 파일이 정상적으로 저장되었는지 확인
        if not os.path.exists(temp_file_path):
            raise FileNotFoundError("파일이 제대로 저장되지 않았습니다.")
            
        with ThreadPoolExecutor() as executor:
            # 비동기 작업으로 파일 업로드
            future = executor.submit(upload_file, temp_file_path, temp_file_name, server_ip, overwrite)
            filename = future.result()
            
            if filename:
                return filename
            else:
                await interaction.followup.send(embed=utils.set_embed("업로드 실패", "이미지 업로드에 실패했습니다. 다시 시도해주세요.", discord.Color.red()), ephemeral=True)
                return None
                
    except Exception as e:
        print(f"이미지 업로드 중 오류: {str(e)}")
        await interaction.followup.send(embed=utils.set_embed("업로드 오류", f"이미지 처리 중 오류가 발생했습니다: {str(e)}", discord.Color.red()), ephemeral=True)
        return None
#-------------------------------------------------------------------------------------------------------------#
# 이미지 업로드 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 텍스트 업로드 함수
#-------------------------------------------------------------------------------------------------------------#
async def upload_text(interaction, server_ip, ref, overwrite: bool = True):
    """
    텍스트를 업로드하고 파일 이름을 반환합니다.
    """    
    subfolder = "prompt"
    
    temp_file_path = os.path.join(os.path.dirname(__file__), "_temp", ref.filename)
    try:
        if isinstance(ref, discord.Attachment):
            await ref.save(temp_file_path)
        else:
            await interaction.followup.send(embed=utils.set_embed("업로드 오류", "텍스트 업로드 중 오류가 발생했습니다: {str(e)}", discord.Color.red()), ephemeral=True)
            return

        # 파일이 정상적으로 저장되었는지 확인
        if not os.path.exists(temp_file_path):
            await interaction.followup.send(embed=utils.set_embed("업로드 오류", f"텍스트 업로드 중 오류가 발생했습니다: {str(e)}", discord.Color.red()), ephemeral=True)
            raise Exception("텍스트 업로드 중 오류가 발생했습니다.")
            
        try:
            with ThreadPoolExecutor() as executor:
                # 비동기 작업으로 파일 업로드
                future = executor.submit(upload_file, temp_file_path, ref.filename, server_ip, overwrite, subfolder)
                filename = future.result()
            
            if filename:
                return filename
            else:
                await interaction.followup.send(embed=utils.set_embed("업로드 실패", "텍스트 업로드에 실패했습니다. 다시 시도해주세요.", discord.Color.red()), ephemeral=True)
                return None
        except Exception as e:
            await interaction.followup.send(embed=utils.set_embed("업로드 오류", "텍스트 업로드 중 오류가 발생했습니다: {str(e)}", discord.Color.red()), ephemeral=True)
            return None
    
    except Exception as e:
        await interaction.followup.send(embed=utils.set_embed("업로드 오류", "텍스트 업로드 중 오류가 발생했습니다: {str(e)}", discord.Color.red()), ephemeral=True)
        return
        
#-------------------------------------------------------------------------------------------------------------#
# 텍스트 업로드 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 캐릭터 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------# 
async def character_1st_process_generate_command(interaction, shot, gender, age, nationality, body_type, hair_color, hair_length, face_shape, seed):
    """
    캐릭터 생성 처리 함수
    """
    # 서버 설정 확인
    server_ip = await check_server_setting(interaction)
    if server_ip is None:
        return
    
    dict_age = {
        "early 20s": ["18", "20", "22"],
        "late 20s": ["24","26", "28"],
        "30s": ["30", "32", "34", "36", "38"],
        "40s": ["40", "42", "44", "46", "48"],
        "50s": ["50", "52", "54", "56", "58"],
        "60s": ["60", "62", "64", "66", "68"],
        "senior": ["70", "72", "74", "76", "78", "80", "82", "84", "86", "88", "90"],
        "random 🎲": "random"
    }
    age_value = random.choice(dict_age[age.value])
    
    # 이 함수에서 생성에 사용하는 매개변수들을 하나의 딕셔너리로 저장
    generation_params = {
        "shot": shot,
        "gender": gender,
        "age": age,
        "age_value": age_value,
        "nationality": nationality,
        "body_type": body_type,
        "hair_color": hair_color,
        "hair_length": hair_length,
        "face_shape": face_shape,
        "seed": seed
    }
    
    # 캐릭터 생성기 초기화
    generator = CharacterGenerator(server_ip)
    
    # 콜백 관리자 생성
    callback_manager = ImageCallbackManager(server_ip, generation_params)
    
    # 이미지 생성 실행
    image_files, image_paths, load_prompt_text, used_seed = await generator.generate(interaction, generation_params, None)
    
    if not image_files:
        return
    
    # 콜백 매니저에 프롬프트 텍스트 추가 (업스케일링에 사용)
    callback_manager.update_params({"prompt_text": load_prompt_text})
    
    # 다음 단계 함수 정의
    async def next_stage(interaction, **kwargs):
        selected_image_path = kwargs.get('selected_image_path')
        if selected_image_path:
            print(f"다음 단계로 진행: 선택된 이미지 경로 = {selected_image_path}")
        
    # 업스케일링 함수 정의
    async def upscale_image(interaction, selected_image_path, prompt_text):
        print(f"업스케일링 진행: 선택된 이미지 경로 = {selected_image_path}")
        await upscaling_process_generate_command(interaction, selected_image_path, prompt_text)
    
    # 이미지가 있는지 확인
    if image_files:
        description = f"캐릭터 특성: \nshot: {shot.name}\ngender: {gender.name}\nage: {age.name}\nnationality: {nationality.value}\nbody_type: {body_type.name}\nhair_color: {hair_color.name}\nhair_length: {hair_length.name}\nseed: {used_seed}"
        embed = utils.set_embed("캐릭터 초기 이미지 생성 완료", description, discord.Color.blue())
        
        # 콜백 함수를 사용하여 뷰 생성
        view = callback_manager.create_view(
            image_files=image_files,
            image_paths=image_paths,
            description=description,
            retry_function=generator.generate,
            upscale_function=upscale_image,
            next_function=next_stage
        )
        
        await interaction.followup.send(embed=embed, files=image_files, view=view, ephemeral=True)
    else:
        # 이미지가 없는 경우
        warning = utils.set_embed("이미지 생성 완료", "이미지 생성은 완료되었으나 결과 이미지를 찾을 수 없습니다.", discord.Color.gold())
        await interaction.followup.send(embed=warning)
#-------------------------------------------------------------------------------------------------------------#
# 캐릭터 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 캐릭터 생성 2차 처리 함수
#-------------------------------------------------------------------------------------------------------------#
async def upscaling_process_generate_command(interaction, ref:str, prompt_text:str):
    
    if ref is None:
        failed = utils.set_embed("이미지 필요", "이미지->이미지 변환을 위해서는 이미지를 첨부해야 합니다.", discord.Color.red())
        await interaction.followup.send(embed=failed, ephemeral=True)
        return
    
    server_ip = await check_server_setting(interaction)
    if server_ip is None:
        return
    
    ref_file_name = await upload_image(interaction, server_ip, ref)
    if ref_file_name is None:
        return
    
    # 생성 파라미터 저장 (재시도를 위한 데이터)
    generation_params = {
        "ref_file_name": ref_file_name,
        "prompt_text": prompt_text,
        "text_file_name": None  # 프롬프트 텍스트를 직접 제공하므로 파일명은 필요없음
    }
    
    # UpscalingGenerator 인스턴스 생성
    generator = UpscalingGenerator(server_ip)
    
    # 콜백 관리자 생성
    callback_manager = ImageCallbackManager(server_ip, generation_params)
    
    # 이미지 생성 실행
    image_files, image_paths, prompt_text, seed_value = await generator.generate(interaction, generation_params)
    
    if not image_files:
        return
    
    # 설명 텍스트 생성
    description = f"업스케일링 완료\n프롬프트: {prompt_text}\n시드: {seed_value}"
    
    # 이미지 뷰 생성 및 표시
    embed = utils.set_embed("업스케일링 완료", description, discord.Color.green())
    
    # 콜백 함수를 사용하여 뷰 생성
    view = callback_manager.create_view(
        image_files=image_files,
        image_paths=image_paths,
        description=description,
        retry_function=generator.generate,
        is_next_button_visible=False
    )
    
    await interaction.followup.send(embed=embed, files=image_files, view=view, ephemeral=True)
#-------------------------------------------------------------------------------------------------------------#
# 캐릭터 생성 2차 처리 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 캐릭터 T 포즈 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#
async def character_t_pose_process_generate_command(interaction, positive_body_type: discord.app_commands.Choice[str], positive_hair: discord.app_commands.Choice[str], positive_wearing:str, positive_shoes:str, ref: discord.Attachment, anime_style:bool):
    # 이미지 필요 확인
    if ref is None:
        failed = utils.set_embed("이미지 필요", "이미지->이미지 변환을 위해서는 이미지를 첨부해야 합니다.", discord.Color.red())
        await interaction.followup.send(embed=failed, ephemeral=True)
        return
    
    # 서버 설정 확인
    server_ip = await check_server_setting(interaction)
    if server_ip is None:
        return
    
    # 이미지 업로드
    ref_file_name = await upload_image(interaction, server_ip, ref)
    if ref_file_name is None:
        return
    
    # 생성 매개변수를 재사용을 위해 딕셔너리로 저장
    generation_params = {
        "positive_body_type": positive_body_type,
        "positive_hair": positive_hair,
        "positive_wearing": positive_wearing,
        "positive_shoes": positive_shoes,
        "ref_file_name": ref_file_name,
        "anime_style": anime_style,
        "needs_multiple_seeds": True,  # 여러 시드가 필요함을 표시
        "seed_count": 4  # 사용할 시드 개수
    }
    
    # T-Pose 생성기 초기화
    generator = TPoseGenerator(server_ip)
    
    # 콜백 관리자 생성
    callback_manager = ImageCallbackManager(server_ip, generation_params)
    
    # 이미지 생성 실행
    image_files, image_paths, load_prompt_text, seed_values = await generator.generate(interaction, generation_params, None)
    
    if not image_files:
        return
    
    # 콜백 매니저에 프롬프트 텍스트 추가 (업스케일링에 사용)
    callback_manager.update_params({"prompt_text": load_prompt_text})
    
    # 업스케일링 함수 정의
    async def upscale_image(interaction, selected_image_path, prompt_text):
        print(f"업스케일링 진행: 선택된 이미지 경로 = {selected_image_path}")
        await upscaling_process_generate_command(interaction, selected_image_path, prompt_text)
    
    # 이미지가 있는지 확인
    if image_files:
        description = f"T-Pose 특성: \n체형: {positive_body_type.name}\n머리 스타일: {positive_hair.name}\n의상: {positive_wearing}\n신발: {positive_shoes}\n애니메이션 스타일: {'적용' if anime_style else '미적용'}"
        embed = utils.set_embed("캐릭터 T-Pose 생성 완료", description, discord.Color.green())
        
        # 콜백 함수를 사용하여 뷰 생성
        view = callback_manager.create_view(
            image_files=image_files,
            image_paths=image_paths,
            description=description,
            retry_function=generator.generate,
            upscale_function=upscale_image
        )
        
        await interaction.followup.send(embed=embed, files=image_files, view=view, ephemeral=True)
    else:
        # 이미지가 없는 경우
        warning = utils.set_embed("이미지 생성 완료", "이미지 생성은 완료되었으나 결과 이미지를 찾을 수 없습니다.", discord.Color.gold())
        await interaction.followup.send(embed=warning, ephemeral=True)
#-------------------------------------------------------------------------------------------------------------#
# 캐릭터 T 포즈 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 애니메이션 캐릭터 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#
async def anime_character_process_generate_command(interaction, ref:discord.Attachment, seed:int = None):
    if ref is None:
        failed = utils.set_embed("이미지 필요", "이미지->이미지 변환을 위해서는 이미지를 첨부해야 합니다.", discord.Color.red())
        await interaction.followup.send(embed=failed, ephemeral=True)
        return
    
    server_ip = await check_server_setting(interaction)
    if server_ip is None:
        return
    
    ref_file_name = await upload_image(interaction, server_ip, ref)
    if ref_file_name is None:
        return
    
    # 생성 매개변수를 재사용을 위해 딕셔너리로 저장
    generation_params = {
        "ref_file_name": ref_file_name,
        "seed": seed,
        "needs_multiple_seeds": True,  # 여러 시드가 필요함을 표시
        "seed_count": 4  # 사용할 시드 개수
    }
    
    # 애니메이션 캐릭터 생성기 초기화
    generator = AnimeCharacterGenerator(server_ip)
    
    # 콜백 관리자 생성
    callback_manager = ImageCallbackManager(server_ip, generation_params)
    
    # 이미지 생성 실행
    image_files, image_paths, load_prompt_text, seed_values = await generator.generate(interaction, generation_params, None)
    
    if not image_files:
        return
    
    # 콜백 매니저에 프롬프트 텍스트 추가 (업스케일링에 사용)
    callback_manager.update_params({"prompt_text": load_prompt_text})
    
    # 업스케일링 함수 정의
    async def upscale_image(interaction, selected_image_path, prompt_text):
        print(f"업스케일링 진행: 선택된 이미지 경로 = {selected_image_path}")
        await upscaling_process_generate_command(interaction, selected_image_path, prompt_text)
    
    # 이미지가 있는지 확인
    if image_files:
        # 시드 값을 문자열로 변환하여 표시
        seed_str = ", ".join(map(str, seed_values)) if isinstance(seed_values, list) else str(seed_values)
        description = f"seed: {seed_str}"
        embed = utils.set_embed("애니메이션 캐릭터 생성 완료", description, discord.Color.blue())
        
        # 콜백 함수를 사용하여 뷰 생성
        view = callback_manager.create_view(
            image_files=image_files,
            image_paths=image_paths,
            description=description,
            retry_function=generator.generate,
            upscale_function=upscale_image
        )
        
        await interaction.followup.send(embed=embed, files=image_files, view=view, ephemeral=True)
    else:
        # 이미지가 없는 경우
        warning = utils.set_embed("이미지 생성 완료", "이미지 생성은 완료되었으나 결과 이미지를 찾을 수 없습니다.", discord.Color.gold())
        await interaction.followup.send(embed=warning, ephemeral=True)
#-------------------------------------------------------------------------------------------------------------#
# 애니메이션 캐릭터 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 멀티뷰 생성 1차 처리 함수
#-------------------------------------------------------------------------------------------------------------#
async def multiview_character_1st_process_generate_command(interaction, ref:discord.Attachment, anime_style:bool):
    if ref is None:
        failed_embed = utils.set_embed("이미지 필요", "이미지->이미지 변환을 위해서는 이미지를 첨부해야 합니다.", discord.Color.red())
        await interaction.followup.send(embed=failed_embed, ephemeral=True)
        return
        
    server_ip = await check_server_setting(interaction)
    if server_ip is None:
        return
        
    # 이미지 업로드
    ref_file_name = await upload_image(interaction, server_ip, ref)
    if ref_file_name is None:
        return
    
    print(f"업로드된 파일: {ref_file_name}")
    
    # 생성 매개변수를 재사용을 위해 딕셔너리로 저장
    generation_params = {
        "ref_file_name": ref_file_name,
        "anime_style": anime_style,
        "ref": ref,  # 원본 참조 이미지 저장
        "needs_multiple_seeds": True,  # 여러 시드가 필요함을 표시
        "seed_count": 4  # 사용할 시드 개수
    }
    
    # 멀티뷰 캐릭터 1단계 생성기 초기화
    generator = MultiviewCharacter1stGenerator(server_ip)
    
    # 콜백 관리자 생성
    callback_manager = ImageCallbackManager(server_ip, generation_params)
    
    # 이미지 생성 실행
    image_files, image_paths, load_prompt_text, seed_values = await generator.generate(interaction, generation_params, None)
    
    if not image_files:
        return
    
    # 콜백 매니저에 프롬프트 텍스트 업데이트
    callback_manager.update_params({"prompt_text": load_prompt_text})
    
    # 다음 단계 함수 정의
    async def next_stage(interaction, **kwargs):
        selected_image_path = kwargs.get('selected_image_path')
        if selected_image_path:
            print(f"다음 단계로 진행: 선택된 이미지 경로 = {selected_image_path}")
            
            # 2단계 함수 호출
            await multiview_character_2nd_process_generate_command(
                interaction, 
                ref=generation_params["ref"],  # 원본 참조 이미지 전달
                ref_sheet=selected_image_path,  # 선택된 이미지 경로 전달
                prompt_text=load_prompt_text,  # 프롬프트 텍스트 전달
                anime_style=generation_params["anime_style"]  # 스타일 설정 전달
            )
    
    # 이미지가 있는지 확인
    if image_files:
        description = f"prompt: {load_prompt_text}"
        
        # 콜백 함수를 사용하여 뷰 생성
        view = callback_manager.create_view(
            image_files=image_files,
            image_paths=image_paths,
            description=description,
            retry_function=generator.generate,
            next_function=next_stage
        )
        
        # 이미지와 버튼을 함께 전송
        success_embed = utils.set_embed("다중 시점 생성 - 1단계 완료", f"원하는 캐릭터 이미지를 선택한 후 '다음' 버튼을 클릭하세요.\n\n{description}", discord.Color.green())
        await interaction.followup.send(embed=success_embed, files=image_files, view=view, ephemeral=True)
    else:
        # 이미지가 없는 경우
        warning_embed = utils.set_embed("이미지 생성 완료", "이미지 생성은 완료되었으나 결과 이미지를 찾을 수 없습니다.", discord.Color.gold())
        await interaction.followup.send(embed=warning_embed, ephemeral=True)
#-------------------------------------------------------------------------------------------------------------#
# 멀티뷰 생성 1차 처리 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 멀티뷰 생성 2차 처리 함수
#-------------------------------------------------------------------------------------------------------------#
async def multiview_character_2nd_process_generate_command(interaction, ref:discord.Attachment, ref_sheet:str, prompt_text:str, anime_style:bool):
    """다중 시점 캐릭터 생성의 두 번째 단계 - 선택된 이미지를 기반으로 ControlNet 처리"""
    
    # 서버 설정 확인
    server_ip = await check_server_setting(interaction)
    if server_ip is None:
        return
    
    ref_file_name = await upload_image(interaction, server_ip, ref)
    if ref_file_name is None:
        return
    
    ref_sheet_file_name = await upload_image(interaction, server_ip, ref_sheet)
    if ref_sheet_file_name is None:
        return
            
    # 진행 메시지 전송
    progress_embed = utils.set_embed(
        "다중 시점 생성 - 2단계", 
        "선택한 이미지를 기반으로 다른 각도의 이미지를 생성하는 중...", 
        discord.Color.blue()
    )
    await interaction.followup.send(embed=progress_embed, ephemeral=True)
    
    # 생성 파라미터 저장
    generation_params = {
        "ref": ref,
        "ref_file_name": ref_file_name,
        "ref_sheet": ref_sheet,
        "ref_sheet_file_name": ref_sheet_file_name,
        "prompt_text": prompt_text,
        "anime_style": anime_style,
        "needs_multiple_seeds": True,
        "seed_count": 3
    }
    
    # 멀티뷰 캐릭터 2단계 생성기 초기화
    generator = MultiviewCharacter2ndGenerator(server_ip)
    
    # 콜백 관리자 생성
    callback_manager = ImageCallbackManager(server_ip, generation_params)
    
    # 이미지 생성 실행
    image_files, image_paths, load_prompt_text, seed_values = await generator.generate(interaction, generation_params, None)
    
    # 결과 표시
    if image_files:
        description = f"seed: {seed_values[0] if isinstance(seed_values, list) else seed_values} prompt: {load_prompt_text}"
        
        # 콜백 함수를 사용하여 뷰 생성
        view = callback_manager.create_view(
            image_files=image_files,
            image_paths=image_paths,
            description=description,
            retry_function=generator.generate,
            is_next_button_visible=False
        )
        
        # 이미지와 버튼을 함께 전송
        success_embed = utils.set_embed("다중 시점 생성 완료", description, discord.Color.green())
        await interaction.followup.send(embed=success_embed, files=image_files, view=view, ephemeral=True)
    else:
        # 이미지가 없는 경우
        warning_embed = utils.set_embed("이미지 생성 완료", "이미지 생성은 완료되었으나 결과 이미지를 찾을 수 없습니다.", discord.Color.gold())
        await interaction.followup.send(embed=warning_embed, ephemeral=True)
#-------------------------------------------------------------------------------------------------------------#
# 멀티뷰 생성 2차 처리 함수
#-------------------------------------------------------------------------------------------------------------#

async def storyboard_prompt_generate_command(interaction, ref:discord.Attachment):
    
    excel_file_path = os.path.join(os.path.dirname(__file__), "_storyboard", "_excel", ref.filename)
    print(f"엑셀 파일 경로 : {excel_file_path}")
    
    try:
        # ref가 discord.Attachment 객체인 경우
        if isinstance(ref, discord.Attachment):
            # 파일 다운로드 및 저장
            await ref.save(excel_file_path)
        # 파일이 정상적으로 저장되었는지 확인
        if not os.path.exists(excel_file_path):
            raise FileNotFoundError("파일이 제대로 저장되지 않았습니다.")
            
        json_file_name = utils.set_file_name(interaction, "json")
        await interaction.followup.send(embed=utils.set_embed("텍스트 생성 중", "텍스트를 생성하는 중입니다.\n\n텍스트 생성이 완료되면 이미지 생성을 시작합니다.", discord.Color.blue()), ephemeral=True)
        json_file_path = await process_txt(excel_file_path, json_file_name)
        print(f"텍스트 파일 경로 : {json_file_path}")
        
        await interaction.followup.send(embed=utils.set_embed("텍스트 생성 완료", "텍스트 생성이 완료되었습니다.", discord.Color.green()), file=discord.File(json_file_path), ephemeral=True)
    except Exception as e:
        print(f"텍스트 업로드 중 오류: {str(e)}")
        await interaction.followup.send(embed=utils.set_embed("업로드 오류", f"텍스트 처리 중 오류가 발생했습니다: {str(e)}", discord.Color.red()), ephemeral=True)
        return None
    

#-------------------------------------------------------------------------------------------------------------#
# 스토리보드 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#
async def storyboard_process_generate_command(interaction, ref:discord.Attachment):
    server_ip = await check_server_setting(interaction)
    if server_ip is None:
        return
   
    if ref is None:
        return
    
    try:
        ref_file_name = await upload_text(interaction, server_ip, ref)
        if ref_file_name is None:
            return
        
        generation_params = {
            "prompt_file_name": ref_file_name
        }
        
        # 스토리보드 생성기 초기화
        generator = StoryBoardGenerator(server_ip)
        
        # 콜백 관리자 생성
        callback_manager = ImageCallbackManager(server_ip, generation_params)
        
        # 이미지 생성 실행
        image_files, image_paths, load_prompt_text, seed_values = await generator.generate(interaction, generation_params, None)
        
        if not image_files:
            return
            
        # 이미지가 10개 이상인 경우 처리 (Discord 제한)
        description = f"seed: {seed_values[0] if isinstance(seed_values, list) else seed_values} prompt: {load_prompt_text}"
        success_embed = utils.set_embed("스토리보드 생성 완료", description, discord.Color.green())
        
        # 10개씩 나누어 전송
        for i in range(0, len(image_files), 10):
            batch_files = image_files[i:i+10]
            batch_paths = {k: v for k, v in image_paths.items() if k.split('_')[1] in [str(j % len(image_files)) for j in range(i, i+10)]}
            
            # 마지막 배치에만 뷰 추가
            if i + 10 >= len(image_files):
                view = callback_manager.create_view(
                    image_files=image_files,  # 전체 이미지 파일 정보는 유지
                    image_paths=image_paths,  # 전체 경로 정보도 유지
                    description=description,
                    retry_function=generator.generate,
                    is_next_button_visible=False
                )
                await interaction.followup.send(
                    embed=success_embed, 
                    files=batch_files, 
                    view=view, 
                    ephemeral=True,
                    content=f"이미지 {i+1}-{i+len(batch_files)}/{len(image_files)}"
                )
            else:
                await interaction.followup.send(
                    embed=success_embed, 
                    files=batch_files, 
                    ephemeral=True,
                    content=f"이미지 {i+1}-{i+len(batch_files)}/{len(image_files)}"
                )
        else:
            # 이미지가 없는 경우
            warning_embed = utils.set_embed("이미지 생성 완료", "이미지 생성은 완료되었으나 결과 이미지를 찾을 수 없습니다.", discord.Color.gold())
            await interaction.followup.send(embed=warning_embed, ephemeral=True)
    except Exception as e:
        print(f"스토리보드 생성 중 오류: {str(e)}")
        await interaction.followup.send(embed=utils.set_embed("업로드 오류", f"스토리보드 생성 중 오류가 발생했습니다: {str(e)}", discord.Color.red()), ephemeral=True)
        return None
    
    pass

#-------------------------------------------------------------------------------------------------------------#
# 이미지->이미지 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#
async def i2i_process_generate_command(interaction, model, positive, ref, ref_weight, seed):
    """
    이미지->이미지 생성 처리 함수
    """
    # 이미지 필요 확인
    if ref is None:
        failed = utils.set_embed("이미지 필요", "이미지->이미지 변환을 위해서는 이미지를 첨부해야 합니다.", discord.Color.red())
        await interaction.followup.send(embed=failed, ephemeral=True)
        return
    
    # 서버 설정 확인
    server_ip = await check_server_setting(interaction)
    if server_ip is None:
        return
    
    # 이미지 업로드
    ref_file_name = await upload_image(interaction, server_ip, ref)
    if ref_file_name is None:
        return
    
    # 생성 파라미터 저장
    generation_params = {
        "model": model,
        "positive": positive,
        "ref_file_name": ref_file_name,
        "ref_weight": ref_weight,
        "seed": seed,
        "prompt_text": positive  # 업스케일링에 사용할 프롬프트 텍스트
    }
    
    # I2I 생성기 초기화
    generator = I2IGenerator(server_ip)
    
    # 콜백 관리자 생성
    callback_manager = ImageCallbackManager(server_ip, generation_params)
    
    # 이미지 생성 실행
    image_files, image_paths, prompt_text, seed_value = await generator.generate(interaction, generation_params, None)
    
    # 결과 표시
    if image_files:
        description = f"워크플로우: {generator.workflow_name}\n모델: {model.value}\n긍정 프롬프트: {positive}\nseed: {seed_value}\n참조 가중치: {ref_weight}"
        embed = utils.set_embed(
            "이미지 생성 완료", 
            description, 
            discord.Color.green()
        )
        
        # 콜백 함수를 사용하여 뷰 생성
        view = callback_manager.create_view(
            image_files=image_files,
            image_paths=image_paths,
            description=description,
            retry_function=generator.generate,
            upscale_function=upscaling_process_generate_command
        )
        
        await interaction.followup.send(embed=embed, files=image_files, view=view, ephemeral=True)
    else:
        # 이미지가 없는 경우
        warning = utils.set_embed("이미지 생성 완료", "이미지 생성은 완료되었으나 결과 이미지를 찾을 수 없습니다.", discord.Color.gold())
        await interaction.followup.send(embed=warning, ephemeral=True)
#-------------------------------------------------------------------------------------------------------------#
# 이미지->이미지 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# 텍스트->이미지 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#
async def t2i_process_generate_command(interaction, model, positive, ratio, seed):
    """
    텍스트->이미지 생성 처리 함수
    """
    # 서버 설정 확인
    server_ip = await check_server_setting(interaction)
    if server_ip is None:
        return
    
    # 생성 파라미터 저장
    generation_params = {
        "model": model,
        "positive": positive,
        "ratio": ratio,
        "seed": seed,
        "prompt_text": positive  # 업스케일링에 사용할 프롬프트 텍스트
    }
    
    # T2I 생성기 초기화
    from image_generators import T2IGenerator
    generator = T2IGenerator(server_ip)
    
    # 콜백 관리자 생성
    from image_callbacks import ImageCallbackManager
    callback_manager = ImageCallbackManager(server_ip, generation_params)
    
    # 이미지 생성 실행
    image_files, image_paths, prompt_text, seed_value = await generator.generate(interaction, generation_params, None)
    
    # 이미지가 있는지 확인
    if image_files:
        description = f"워크플로우: {generator.workflow_name}\n모델: {model.value}\n긍정 프롬프트: {positive}\nseed: {seed_value}"
        embed = utils.set_embed(
            "이미지 생성 완료", 
            description, 
            discord.Color.green()
        )
        
        # 콜백 함수를 사용하여 뷰 생성
        view = callback_manager.create_view(
            image_files=image_files,
            image_paths=image_paths,
            description=description,
            retry_function=generator.generate,
            upscale_function=upscaling_process_generate_command
        )
        
        await interaction.followup.send(embed=embed, files=image_files, view=view, ephemeral=True)
    else:
        # 이미지가 없는 경우
        warning = utils.set_embed("이미지 생성 완료", "이미지 생성은 완료되었으나 결과 이미지를 찾을 수 없습니다.", discord.Color.gold())
        await interaction.followup.send(embed=warning, ephemeral=True)
#-------------------------------------------------------------------------------------------------------------#
# 텍스트->이미지 생성 처리 함수
#-------------------------------------------------------------------------------------------------------------#

#-------------------------------------------------------------------------------------------------------------#
# ComfyUI 프롬프트 매소드를 비동기 방식으로 수정
#-------------------------------------------------------------------------------------------------------------#
async def queue_prompt(ip,prompt, port=8000, interaction=None, timeout=180):
    # 진행률 업데이트를 위한 메시지 객체
    progress_message = None
    update_event = threading.Event()
    progress_queue = Queue()

    if interaction:
        # 초기 진행률 메시지 생성
        embed = utils.set_embed(
            "이미지 생성 중...", 
            f"{generate_progress_bar(0)}\n**진행률**: 0/0 (0%)", 
            discord.Color.blue()
        )
        progress_message = await interaction.followup.send(embed=embed, ephemeral=True)
        # 사용자 ID로 진행률 메시지 저장    
        progress_messages[interaction.user.id] = progress_message
    
    # 진행률 업데이트 함수
    async def update_progress_loop():
        last_update_time = 0
        last_percentage = -1  # 이전 업데이트와 다를 때만 업데이트하기 위한 변수
        current_step = 0
        total_steps = 1  # 0으로 나누기 방지

        while not update_event.is_set():
            current_time = time.time()
            progress_updated = False
            
            # 진행률 정보 확인
            if not progress_queue.empty():
                value, max_val = progress_queue.get()
                current_step = value
                total_steps = max_val
                percentage = int((value / max_val) * 100)
                
                # 이전 업데이트와 다르거나 마지막 업데이트 후 일정 시간이 지났을 때만 업데이트
                if percentage != last_percentage or current_time - last_update_time > 2:
                    last_percentage = percentage
                    progress_updated = True
            
            # 업데이트 수행
            if progress_updated and progress_message:
                try:
                    await update_progress_message(progress_message, current_step, total_steps)
                    last_update_time = current_time
                except Exception as e:
                    print(f"진행률 메시지 업데이트 중 오류: {str(e)}")
            
            # 잠시 대기
            await asyncio.sleep(0.5)
    
    # 진행률 업데이트 루프 시작
    if interaction:
        asyncio.create_task(update_progress_loop())
    
    # 실행 함수 정의 - 이 함수는 별도 스레드에서 동기적으로 실행됨
    def run_comfyui(timeout_value):
        try:
            # ComfyUI 웹 클라이언트 생성
            print(f"ComfyUI 연결 초기화: {ip}:{port} (클라이언트 생성)")
            comfy_client = comfyui_web(ip, port)
            
            # 진행률 업데이트를 위한 콜백 함수
            def progress_callback(value, max_val):
                if interaction:
                    progress_queue.put((value, max_val))
            
            # 클라이언트에 콜백 설정
            comfy_client.set_progress_callback(progress_callback)
            
            # 프롬프트 설정         
            comfy_client.select_prompt(prompt)
            
            # 디버그 메시지 - 워크플로우 내 SaveImageWebsocket 노드 확인
            has_websocket_node = False
            if isinstance(prompt, dict):
                for node_id, node in prompt.items():
                    if isinstance(node, dict) and node.get("class_type") == "SaveImageWebsocket":
                        has_websocket_node = True
                        print(f"SaveImageWebsocket 노드가 워크플로우에 이미 존재합니다 (ID: {node_id})")
                        break
            
            if not has_websocket_node:
                print("SaveImageWebsocket 노드가 없어 자동으로 추가됩니다")
            
            print(f"ComfyUI 연결 시도: {ip}:{port} (run 메소드 호출), 타임아웃: {timeout_value}초")
            result = comfy_client.run(timeout_value)
            
            # 결과 디버그
            if isinstance(result, dict) and "error" in result:
                print(f"ComfyUI 오류 발생: {result['error']}")
            elif isinstance(result, dict):
                image_count = 0
                for node_id, images in result.items():
                    image_count += len(images)
                print(f"이미지 생성 완료: {image_count}개의 이미지를 받았습니다")
            


            return result
            
        except Exception as e:
            print(f"Error in queue_prompt: {e}")
            import traceback
            traceback.print_exc()  # 더 자세한 오류 정보 출력
            return {"error": f"오류 발생: {str(e)}"}
        finally:
            # 진행률 업데이트 종료
            update_event.set()
    
    # 별도의 스레드 풀에서 시간이 오래 걸리는 동기 작업 실행
    with ThreadPoolExecutor() as pool:
        result = await asyncio.get_event_loop().run_in_executor(pool, run_comfyui, timeout)
        
    # 작업 완료 시 진행률 100%로 업데이트
    if interaction and progress_message:
        if isinstance(result, dict) and "error" in result:
            # 오류 발생 시 진행률 메시지 업데이트
            error_embed = utils.set_embed(
                "이미지 생성 실패", 
                f"오류: {result['error']}", 
                discord.Color.red()
            )
            await progress_message.edit(embed=error_embed)
        else:
            # 성공 시 진행률 100%로 업데이트
            success_embed = utils.set_embed(
                "이미지 생성 완료", 
                f"{generate_progress_bar(100)}\n**진행률**: 100/100 (100%)", 
                discord.Color.green()
            )
            await progress_message.edit(embed=success_embed)
        
        # 진행률 메시지 저장소에서 제거
        if interaction.user.id in progress_messages:
            del progress_messages[interaction.user.id]
    
    return result