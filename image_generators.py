import os
import json
import random
from image_generator import ImageGenerator
import discord
import utils

class T2IGenerator(ImageGenerator):
    """텍스트-이미지(T2I) 생성기"""
    
    def __init__(self, server_ip):
        super().__init__(server_ip, "t2i_flux1.0_dev.json")
        self.timeout = 180  # T2I 프로세스의 타임아웃 설정
        
    def prepare_prompt(self, prompt, params, seed_value):
        """T2I 워크플로우 프롬프트 준비"""
        # 이미지 비율 데이터 로드
        ratio_data = {}
        try:
            ratio_path = os.path.join(os.path.dirname(__file__), '_comfyui_info', 'output_ratio.json')
            with open(ratio_path, 'r') as f:
                ratio_data = json.load(f)
                
            # 선택된 비율 값 사용
            ratio_key = params['ratio'].value
            width = int(ratio_data[ratio_key]['width'])
            height = int(ratio_data[ratio_key]['height'])
        except Exception as e:
            print(f"Error accessing ratio data: {e}")
            width, height = 1024, 1024  # 기본값
        
        text_file_name = f"t2i_{seed_value}.txt"
        params["text_file_name"] = text_file_name  # 텍스트 파일명 저장
        
        # 노드별 파라미터 설정
        for node_id, node in prompt.items():
            # 텍스트 인코딩
            if node.get("class_type") == "CLIPTextEncode" and node.get("_meta", {}).get("title") == "CLIP Text Encode (Positive Prompt)":
                node["inputs"]["text"] = params["positive"]
                
            # 빈 레이턴트 이미지 (크기 설정)
            elif node.get("class_type") == "EmptyLatentImage" or node.get("class_type") == "EmptySD3LatentImage":
                node["inputs"]["width"] = width
                node["inputs"]["height"] = height
                
            # 샘플러 (시드 설정)
            elif node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = seed_value
                
            # 프롬프트 이름 설정
            elif node.get("class_type") == "easy string" and node.get("_meta", {}).get("title") == "Prompt Name":
                node["inputs"]["value"] = text_file_name

class I2IGenerator(ImageGenerator):
    """이미지-이미지(I2I) 생성기"""
    
    def __init__(self, server_ip):
        super().__init__(server_ip, "i2i_flux1.0_dev.json")
        self.timeout = 180  # I2I 프로세스의 타임아웃 설정
        
    def prepare_prompt(self, prompt, params, seed_value):
        """I2I 워크플로우 프롬프트 준비"""
        # 노드별 파라미터 설정
        for node_id, node in prompt.items():
            # 텍스트 인코딩
            if node.get("class_type") == "CLIPTextEncode" and node.get("_meta", {}).get("title") == "CLIP Text Encode (Positive Prompt)":
                node["inputs"]["text"] = params["positive"]
                
            # 참조 이미지 설정
            elif node.get("class_type") == "LoadImage" and node.get("_meta", {}).get("title") == "Ref.":
                node["inputs"]["image"] = f"./upload/{params['ref_file_name']}"
                
            # 샘플러 (시드 및 가중치 설정)
            elif node.get("class_type") == "KSampler":
                node["inputs"]["denoise"] = params["ref_weight"]
                node["inputs"]["seed"] = seed_value

class CharacterGenerator(ImageGenerator):
    """캐릭터 생성기"""
    
    def __init__(self, server_ip):
        super().__init__(server_ip, "photo-realistic_maker_1st.json")
        self.timeout = 300  # 캐릭터 생성 프로세스의 타임아웃 설정
        
    def prepare_prompt(self, prompt, params, seed_value):
        """캐릭터 워크플로우 프롬프트 준비"""
        text_file_name = f"prompt_{str(int(random.randint(1, 1000000)))}.txt"
        params["text_file_name"] = text_file_name  # 텍스트 파일명 저장
        
        # 노드별 파라미터 설정
        for node_id, node in prompt.items():
            # 샘플러 시드 설정
            if node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = seed_value
                
            # 캐릭터 기본 속성
            elif node.get("class_type") == "PortraitMasterBaseCharacter":
                node["inputs"]["shot"] = params["shot"].value
                node["inputs"]["gender"] = params["gender"].value
                node["inputs"]["age"] = params["age_value"]
                node["inputs"]["nationality"] = params["nationality"].value
                node["inputs"]["body_type"] = params["body_type"].value
                node["inputs"]["hair_color"] = params["hair_color"].value
                node["inputs"]["hair_length"] = params["hair_length"].value
                node["inputs"]["face_shape"] = params["face_shape"].value
                
            # 얼굴 디테일러
            elif node.get("class_type") == "FaceDetailer":
                node["inputs"]["seed"] = seed_value
                
            # 프롬프트 이름 설정
            elif node.get("class_type") == "easy string" and node.get("_meta", {}).get("title") == "Prompt Name":
                node["inputs"]["value"] = text_file_name

class MultiviewCharacter1stGenerator(ImageGenerator):
    """멀티뷰 캐릭터 1단계 생성기"""
    
    def __init__(self, server_ip):
        super().__init__(server_ip, "character_multi-view_1st.json")
        self.timeout = 500  # 멀티뷰 1단계 프로세스의 타임아웃 설정
        
    def prepare_prompt(self, prompt, params, seed_values):
        """멀티뷰 1단계 워크플로우 프롬프트 준비"""
        text_file_name = f"prompt_{str(int(random.randint(1, 1000000)))}.txt"
        params["text_file_name"] = text_file_name  # 텍스트 파일명 저장
        
        # 시드 값 확인 (다중 시드 필요)
        if not isinstance(seed_values, list):
            seed_values = [seed_values] * 4  # 단일 값을 4개로 복제
            
        # 스타일 설정
        style = "3d pixar character" if params["anime_style"] else ""
        
        # 노드별 파라미터 설정
        for node_id, node in prompt.items():
            # 업로드 이미지
            if node.get("class_type") == "LoadImage" and node.get("_meta", {}).get("title") == "Upload":
                node["inputs"]["image"] = f"./upload/{params['ref_file_name']}"
                
            # 스타일 설정
            elif node.get("class_type") == "String Literal (Image Saver)" and node.get("_meta", {}).get("title") == "Style":
                node["inputs"]["string"] = style
                
            # 프롬프트 이름 설정
            elif node.get("class_type") == "easy string" and node.get("_meta", {}).get("title") == "Prompt Name":
                node["inputs"]["value"] = text_file_name
                
            # 샘플러 시드 설정 (각 샘플러별)
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler-01":
                node["inputs"]["seed"] = seed_values[0]
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler-02":
                node["inputs"]["seed"] = seed_values[1]
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler-03":
                node["inputs"]["seed"] = seed_values[2]
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler-04":
                node["inputs"]["seed"] = seed_values[3]

class MultiviewCharacter2ndGenerator(ImageGenerator):
    """멀티뷰 캐릭터 2단계 생성기"""
    
    def __init__(self, server_ip):
        super().__init__(server_ip, "character_multi-view_2nd.json")
        self.timeout = 500  # 멀티뷰 2단계 프로세스의 타임아웃 설정
        
    def prepare_prompt(self, prompt, params, seed_values):
        """멀티뷰 2단계 워크플로우 프롬프트 준비"""
        # 시드 값 확인 (다중 시드 필요)
        if not isinstance(seed_values, list):
            seed_values = [seed_values] * 3  # 단일 값을 3개로 복제
            
        # 노드별 파라미터 설정
        for node_id, node in prompt.items():
            # 업로드 이미지
            if node.get("class_type") == "LoadImage" and node.get("_meta", {}).get("title") == "Upload":
                node["inputs"]["image"] = f"./upload/{params['ref_file_name']}"
                
            # 캐릭터 시트 이미지
            elif node.get("class_type") == "LoadImage" and node.get("_meta", {}).get("title") == "Character Sheet":
                node["inputs"]["image"] = f"./upload/{params['ref_sheet_file_name']}"
                
            # 프롬프트 설정
            elif node.get("class_type") == "String Literal (Image Saver)" and node.get("_meta", {}).get("title") == "Prompt":
                node["inputs"]["string"] = params['prompt_text']
                
            # 다양한 샘플러 시드 설정
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler":
                node["inputs"]["seed"] = seed_values[0]
            elif node.get("class_type") == "UltimateSDUpscale" and node.get("_meta", {}).get("title") == "Ultimate SD Upscale":
                node["inputs"]["seed"] = seed_values[1]
            elif node.get("class_type") == "FaceDetailer" and node.get("_meta", {}).get("title") == "FaceDetailer":
                node["inputs"]["seed"] = seed_values[2]

class UpscalingGenerator(ImageGenerator):
    """이미지 업스케일링 생성기"""
    
    def __init__(self, server_ip):
        super().__init__(server_ip, "photo-realistic_maker_2nd.json")
        self.timeout = 360  # 업스케일링 프로세스의 타임아웃 설정
        
    def prepare_prompt(self, prompt, params, seed_value):
        """업스케일링 워크플로우 프롬프트 준비"""
        # 노드별 파라미터 설정
        for node_id, node in prompt.items():
            # 업로드 이미지 설정
            if node.get("class_type") == "LoadImage" and node.get("_meta", {}).get("title") == "Upload":
                node["inputs"]["image"] = f"./upload/{params['ref_file_name']}"
                
            # 프롬프트 텍스트 설정
            elif node.get("class_type") == "CLIPTextEncode" and node.get("_meta", {}).get("title") == "Positive Prompt":
                node["inputs"]["text"] = params["prompt_text"]
                
            # 샘플러 시드 설정
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler":
                node["inputs"]["seed"] = seed_value
                
    async def send_initial_message(self, interaction, message="업스케일링 시작"):
        """업스케일링 진행 메시지 생성"""
        initial_embed = utils.set_embed(
            message, 
            f"이미지 업스케일링 중입니다...", 
            discord.Color.blue()
        )
        await interaction.followup.send(embed=initial_embed, ephemeral=True)

class TPoseGenerator(ImageGenerator):
    """캐릭터 T-Pose 생성기"""
    
    def __init__(self, server_ip):
        super().__init__(server_ip, "t-pose_maker.json")
        self.timeout = 240  # T-Pose 프로세스의 타임아웃 설정
        
    def prepare_prompt(self, prompt, params, seed_values):
        """T-Pose 워크플로우 프롬프트 준비"""
        # 텍스트 파일 이름 생성
        text_file_name = f"prompt_{str(int(random.randint(1, 1000000)))}.txt"
        params["text_file_name"] = text_file_name  # 텍스트 파일명 저장
        
        # 시드 값 확인 (다중 시드 필요)
        if not isinstance(seed_values, list):
            seed_values = [seed_values] * 4  # 단일 값을 4개로 복제
        
        # 노드별 파라미터 설정
        for node_id, node in prompt.items():
            # 업로드된 캐릭터 이미지
            if node.get("class_type") == "LoadImage" and node.get("_meta", {}).get("title") == "UploadCharacter":
                node["inputs"]["image"] = f"./upload/{params['ref_file_name']}"
                
            # 각 샘플러 시드 설정
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler_01":
                node["inputs"]["seed"] = seed_values[0]
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler_02":
                node["inputs"]["seed"] = seed_values[1]
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler_03":
                node["inputs"]["seed"] = seed_values[2]
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler_04":
                node["inputs"]["seed"] = seed_values[3]
                
            # 캐릭터 속성 설정
            elif node.get("class_type") == "easy string" and node.get("_meta", {}).get("title") == "BodyType":
                node["inputs"]["value"] = f"({params['positive_body_type'].value}:1.1)"
            elif node.get("class_type") == "easy string" and node.get("_meta", {}).get("title") == "HairType":
                node["inputs"]["value"] = f"({params['positive_hair'].value}:1.1)"
            elif node.get("class_type") == "easy string" and node.get("_meta", {}).get("title") == "Wearing":
                node["inputs"]["value"] = f"({params['positive_wearing']}:1.1)"
            elif node.get("class_type") == "easy string" and node.get("_meta", {}).get("title") == "ShoeType":
                node["inputs"]["value"] = f"({params['positive_shoes']}:1.1)"
                
            # 애니메이션 스타일 설정    
            elif node.get("class_type") == "easy loraStack" and node.get("_meta", {}).get("title") == "EasyLoraStack":
                node["inputs"]["toggle"] = params["anime_style"]
                
            # 프롬프트 이름 설정
            elif node.get("class_type") == "easy string" and node.get("_meta", {}).get("title") == "Prompt Name":
                node["inputs"]["value"] = text_file_name
                
            # 스타일 설정 (애니메이션 스타일일 경우)
            elif node.get("class_type") == "String Literal (Image Saver)" and node.get("_meta", {}).get("title") == "Style":
                if params["anime_style"]:
                    node["inputs"]["string"] = "3d pixar character, 3d rendering character"
                else:
                    node["inputs"]["string"] = ""
    
    async def send_initial_message(self, interaction, message="T-Pose 생성 시작"):
        """T-Pose 진행 메시지 생성"""
        initial_embed = utils.set_embed(
            message, 
            f"캐릭터 T-Pose 생성 중입니다...", 
            discord.Color.blue()
        )
        await interaction.followup.send(embed=initial_embed, ephemeral=True)

class AnimeCharacterGenerator(ImageGenerator):
    """애니메이션 캐릭터 생성기"""
    
    def __init__(self, server_ip):
        super().__init__(server_ip, "anime-3d_character.json")
        self.timeout = 180  # 애니메이션 캐릭터 프로세스의 타임아웃 설정
        
    def prepare_prompt(self, prompt, params, seed_values):
        """애니메이션 캐릭터 워크플로우 프롬프트 준비"""
        # 시드 값 확인 (다중 시드 필요)
        if not isinstance(seed_values, list):
            seed_values = [seed_values] * 4  # 단일 값을 4개로 복제
            
        text_file_name = f"prompt_{str(int(random.randint(1, 1000000)))}.txt"
        params["text_file_name"] = text_file_name  # 텍스트 파일명 저장
        
        # 노드별 파라미터 설정
        for node_id, node in prompt.items():
            # 업로드 이미지 설정
            if node.get("class_type") == "LoadImage" and node.get("_meta", {}).get("title") == "Upload":
                node["inputs"]["image"] = f"./upload/{params['ref_file_name']}"
            
            # 각 샘플러 시드 설정
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler_01":
                node["inputs"]["seed"] = seed_values[0]
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler_02":
                node["inputs"]["seed"] = seed_values[1]
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler_03":
                node["inputs"]["seed"] = seed_values[2]
            elif node.get("class_type") == "KSampler" and node.get("_meta", {}).get("title") == "KSampler_04":
                node["inputs"]["seed"] = seed_values[3]
            
            # 프롬프트 이름 설정
            elif node.get("class_type") == "easy string" and node.get("_meta", {}).get("title") == "Prompt Name":
                node["inputs"]["value"] = text_file_name
    
    async def send_initial_message(self, interaction, message="애니메이션 캐릭터 생성 시작"):
        """애니메이션 캐릭터 진행 메시지 생성"""
        initial_embed = utils.set_embed(
            message, 
            f"애니메이션 캐릭터 이미지 생성 중입니다...", 
            discord.Color.blue()
        )
        await interaction.followup.send(embed=initial_embed, ephemeral=True) 

class StoryBoardGenerator(ImageGenerator):
    """스토리보드 생성기"""
    
    def __init__(self, server_ip):
        super().__init__(server_ip, "storyboard-maker.json")
        self.timeout = 300  # 스토리보드 생성 프로세스의 타임아웃 설정
        
    def prepare_prompt(self, prompt, params, seed_value):
        """스토리보드 워크플로우 프롬프트 준비"""
        # 노드별 파라미터 설정
        for node_id, node in prompt.items():
            # 텍스트 인코딩
            if node.get("class_type") == "JsonParserNode" and node.get("_meta", {}).get("title") == "JsonParserNode":
                node["inputs"]["file_name"] = params["prompt_file_name"]
                