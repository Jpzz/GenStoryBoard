import discord
import os
import json
import random
from abc import ABC, abstractmethod
import utils

class ImageGenerator(ABC):
    """
    이미지 생성 기능을 위한 기본 추상 클래스.
    각 이미지 생성 기능은 이 클래스를 상속받아 구현합니다.
    """
    
    def __init__(self, server_ip, workflow_name=None):
        """
        ImageGenerator 초기화
        
        Args:
            server_ip: ComfyUI 서버 IP
            workflow_name: 사용할 워크플로우 파일명
        """
        self.server_ip = server_ip
        self.workflow_name = workflow_name
        self.timeout = 300  # 기본 타임아웃 값
        
    def set_timeout(self, timeout):
        """타임아웃 값 설정"""
        self.timeout = timeout
        return self
        
    def load_prompt(self):
        """워크플로우 파일을 로드하여 프롬프트 데이터 반환"""
        if not self.workflow_name:
            raise ValueError("workflow_name이 설정되지 않았습니다.")
            
        prompt_path = os.path.join(os.path.dirname(__file__), '_comfyui_workflows', self.workflow_name)
        with open(prompt_path, "r") as f:
            prompt = json.load(f)
        return prompt
    
    async def send_initial_message(self, interaction, message="이미지 생성 시작"):
        """초기 진행률 메시지 생성"""
        initial_embed = utils.set_embed(
            message, 
            f"ComfyUI 서버에 연결 중입니다...", 
            discord.Color.blue()
        )
        await interaction.followup.send(embed=initial_embed, ephemeral=True)
    
    @abstractmethod
    def prepare_prompt(self, prompt, params, seed_value):
        """워크플로우 프롬프트 준비 (추상 메서드)"""
        pass
    
    async def generate(self, interaction, params, new_seed=None):
        """
        이미지 생성 처리의 공통 로직
        
        Args:
            interaction: Discord 인터랙션 객체
            params: 생성 매개변수
            new_seed: 새로운 시드 값(재생성 시 사용)
            
        Returns:
            생성된 이미지 파일, 경로, 프롬프트 텍스트, 사용된 시드 값 등
        """
        from generate_function import queue_prompt, process_result_image, get_view_text
        
        # 워크플로우 프롬프트 로드
        prompt = self.load_prompt()
        
        # 시드 값 설정
        if new_seed is not None:
            seed_value = new_seed
        elif params.get("seed") is not None:
            seed_value = params["seed"]
        else:
            seed_value = random.randint(1, 2147483647)
        
        # 워크플로우 파라미터 설정
        self.prepare_prompt(prompt, params, seed_value)
        
        # 초기 메시지는 첫 생성 시에만 보냄
        if new_seed is None:
            await self.send_initial_message(interaction)
        
        # 프롬프트 전송 및 결과 수신
        result = await queue_prompt(self.server_ip, prompt, 8000, interaction, self.timeout)
        
        if result is None:
            failed = utils.set_embed("프롬프트 전송 실패", "프롬프트 전송 중 오류가 발생했습니다.", discord.Color.red())
            await interaction.followup.send(embed=failed, ephemeral=True)
            return None, None, None, None
        
        # 결과에 에러가 있는지 확인
        if isinstance(result, dict) and "error" in result:
            failed = utils.set_embed("이미지 생성 실패", f"오류: {result['error']}", discord.Color.red())
            await interaction.followup.send(embed=failed, ephemeral=True)
            return None, None, None, None
        
        # 이미지 파일 처리
        image_files, image_paths = process_result_image(result)
        
        # 프롬프트 텍스트 가져오기 (텍스트 파일이 있는 경우)
        text_file_name = params.get("text_file_name", None)
        prompt_text = get_view_text(self.server_ip, text_file_name) if text_file_name else params.get("prompt_text", "")
        
        return image_files, image_paths, prompt_text, seed_value