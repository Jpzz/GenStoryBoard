import discord
from discord.ui import View, Button, Select
import os
from typing import Callable, Optional, Dict, List, Any
import asyncio
import uuid  # 고유 ID 생성을 위해 추가

class ImageView(View):
    """이미지를 표시하기 위한 뷰 클래스 (단일 이미지와 다중 이미지 모두 지원)"""
    
    def __init__(self, image_files=None, image_paths=None, description="", timeout=600, 
                 on_image_change: Optional[Callable[[int, str], Any]] = None,
                 on_next_click:Optional[Callable[[str], Any]] = None,
                 on_retry_click:Optional[Callable[[str], Any]] = None,
                 on_upscale_click:Optional[Callable[[str], Any]] = None,
                 next_button_label: str = "다음 단계",
                 is_next_button_visible: bool = True):
        """
        이미지 뷰 초기화
        
        Args:
            image_files: 이미지 파일 목록 (discord.File 객체)
            image_paths: 이미지 경로가 저장된 딕셔너리 {'img_0': 'path/to/image1.png', ...}
            description: 이미지 설명
            timeout: 뷰 타임아웃 시간
            on_image_change: 이미지 변경 시 호출되는 콜백 함수 (인덱스와 경로를 인자로 받음)
            on_next_click: 다음 버튼 클릭 시 호출되는 콜백 함수 (선택된 이미지 경로를 인자로 받음)
            on_retry_click: 재시도 버튼 클릭 시 호출되는 콜백 함수 (interaction을 인자로 받음)
            on_upscale_click: 업스케일링 버튼 클릭 시 호출되는 콜백 함수 (선택된 이미지 경로를 인자로 받음)
            next_button_label: 다음 버튼에 표시될 텍스트
        """
        super().__init__(timeout=timeout)
        self.image_files = image_files or []
        self.image_paths = image_paths or {}
        self.description = description
        self.total_images = len(self.image_files) if self.image_files else 1
        self.is_multi_image = self.total_images > 1
        self.current_image_index = 0
        self.message_id = None  # 메시지 ID 저장 변수 추가
        self.on_image_change = on_image_change  # 이미지 변경 콜백 저장
        self.on_next_click = on_next_click  # 다음 버튼 콜백 저장
        self.on_retry_click = on_retry_click  # 재시도 버튼 콜백 저장
        self.on_upscale_click = on_upscale_click  # 업스케일링 버튼 콜백 저장
        self.selected_image_data = None  # 콜백에서 반환한 데이터 저장
        self.selected_image_path = None  # 선택된 이미지 경로 저장
        self.view_id = str(uuid.uuid4())[:8]  # 각 뷰 인스턴스에 대한 고유 ID
        self.next_button_label = next_button_label  # 다음 버튼 레이블 저장
        self.is_next_button_visible = is_next_button_visible  # 다음 버튼 표시 여부 저장
        # 저장된 UI 컴포넌트 참조
        self.image_select = None
        self.next_button = None
        self.back_button = None
        self.save_button = None
        self.retry_button = None
        self.upscale_button = None
        # 다중 이미지인 경우 선택기 추가
        if self.is_multi_image:
            self.add_image_select()
            self.add_retry_button()
        else:
            self.add_save_button()
            self.add_upscale_button()
            
        # 초기 이미지 인덱스로 콜백 호출 (비동기로 실행)
        if self.on_image_change and self.image_paths:
            img_key = f"img_{self.current_image_index}"
            if img_key in self.image_paths:
                # 비동기 콜백을 별도의 태스크로 실행
                asyncio.create_task(self._call_image_change_callback(self.current_image_index, self.image_paths[img_key]))

    # 비동기 콜백 호출을 위한 헬퍼 메서드
    async def _call_image_change_callback(self, index, file_path):
        """콜백 함수를 안전하게 호출하고 반환값 저장"""
        if self.on_image_change:
            try:
                # 콜백 함수가 코루틴인 경우 await
                if asyncio.iscoroutinefunction(self.on_image_change):
                    result = await self.on_image_change(index, file_path)
                else:
                    result = self.on_image_change(index, file_path)
                
                # 선택된 이미지 경로 저장
                self.selected_image_path = file_path
                
                # 반환값 저장
                self.selected_image_data = result
                return result
            except Exception as e:
                print(f"콜백 함수 호출 중 오류 발생: {str(e)}")
        return None

    # 이미지 인덱스 변경 메서드
    async def set_current_image(self, index: int):
        """
        현재 이미지 인덱스 설정 및 콜백 호출
        
        Args:
            index: 설정할 이미지 인덱스
            
        Returns:
            콜백 함수의 반환값 또는 성공 여부(bool)
        """
        if 0 <= index < self.total_images:
            self.current_image_index = index
            
            # 콜백 함수 호출
            if f"img_{index}" in self.image_paths:
                result = await self._call_image_change_callback(index, self.image_paths[f"img_{index}"])
                return result
                
            return True
        return False

    #-------------------------------------------------------------------------------------------------------------#
    # 워크플로우 버튼 추가 기능
    #-------------------------------------------------------------------------------------------------------------#
    def add_next_button(self):
        if self.is_next_button_visible:
            self.next_button = Button(
                style=discord.ButtonStyle.primary,
                label=self.next_button_label,
                emoji="➡️",
                custom_id=f"next_{self.view_id}_{uuid.uuid4().hex[:4]}"  # 고유 ID 사용
            )
            self.next_button.callback = self.next_callback
            self.add_item(self.next_button)
        
    def remove_next_button(self):
        if self.is_next_button_visible:
            if self.next_button and self.next_button in self.children:
                self.remove_item(self.next_button)
    
    async def next_callback(self, interaction):
        """다음 버튼 클릭 시 호출되는 콜백"""
        await interaction.response.defer(ephemeral=True)
        
        if self.on_next_click and self.selected_image_path:
            try:
                await self.on_next_click(interaction, self.selected_image_path)
            except Exception as e:
                print(f"다음 버튼 콜백 함수 호출 중 오류: {str(e)}")
                await interaction.followup.send("다음 단계 진행 중 오류가 발생했습니다.", ephemeral=True)
    #-------------------------------------------------------------------------------------------------------------#
    # 워크플로우 버튼 추가 기능
    #-------------------------------------------------------------------------------------------------------------#

    #-------------------------------------------------------------------------------------------------------------#
    # 이전 버튼 추가 기능
    #-------------------------------------------------------------------------------------------------------------#
    def add_back_button(self):
        self.back_button = Button(
            style=discord.ButtonStyle.primary,
            label="이전",
            emoji="⬅️",
            custom_id=f"back_{self.view_id}_{uuid.uuid4().hex[:4]}"  # 고유 ID 사용
        )
        self.back_button.callback = self.back_callback
        self.add_item(self.back_button)
        
    def remove_back_button(self):
        if self.back_button and self.back_button in self.children:
            self.remove_item(self.back_button)
            
    async def back_callback(self, interaction):
        """이전 버튼 클릭 시 호출되는 콜백"""
        await interaction.response.defer(ephemeral=True)
        
        # 이미지 선택 화면으로 돌아감
        self.remove_next_button()
        self.add_image_select()
        self.remove_save_button()
        self.remove_back_button()
        self.add_retry_button()
        self.remove_upscale_button()

        # 모든 이미지 파일 준비
        image_files = []
        for key, path in self.image_paths.items():
            if os.path.exists(path):
                image_files.append(discord.File(path, filename=f"image_{key}.png"))
                
        if image_files:
            try:
                await interaction.edit_original_response(content="이미지를 선택해주세요.", attachments=image_files, view=self)
            except Exception as e:
                print(f"이전 버튼 처리 중 오류: {str(e)}")
                await interaction.followup.send("이미지 목록 표시 중 오류가 발생했습니다.", ephemeral=True)
        else:
            await interaction.followup.send("이미지 파일을 찾을 수 없습니다.", ephemeral=True)
    #-------------------------------------------------------------------------------------------------------------#
    # 이전 버튼 추가 기능
    #-------------------------------------------------------------------------------------------------------------# 

    #-------------------------------------------------------------------------------------------------------------#
    # 재시도 버튼 추가 기능
    #-------------------------------------------------------------------------------------------------------------#
    def add_retry_button(self):
        self.retry_button = Button(
            style=discord.ButtonStyle.primary,
            label="다시 시도",
            emoji="🔄",
            custom_id=f"retry_{self.view_id}_{uuid.uuid4().hex[:4]}"  # 고유 ID 사용
        )
        self.retry_button.callback = self.retry_callback
        self.add_item(self.retry_button)
        
    def remove_retry_button(self):
        if self.retry_button and self.retry_button in self.children:
            self.remove_item(self.retry_button)

    async def retry_callback(self, interaction):
        """다시 시도 버튼 클릭 시 호출되는 콜백"""
        await interaction.response.defer(ephemeral=True)
        
        if self.on_retry_click:
            try:
                # 콜백 함수가 코루틴인 경우 await
                if asyncio.iscoroutinefunction(self.on_retry_click):
                    await self.on_retry_click(interaction)
                else:
                    self.on_retry_click(interaction)
            except Exception as e:
                print(f"재시도 버튼 콜백 함수 호출 중 오류: {str(e)}")
                await interaction.followup.send("이미지 재생성 시도 중 오류가 발생했습니다.", ephemeral=True)
        else:
            await interaction.followup.send("재시도 기능이 설정되지 않았습니다.", ephemeral=True)
    #-------------------------------------------------------------------------------------------------------------#
    # 재시도 버튼 추가 기능
    #-------------------------------------------------------------------------------------------------------------#

    def add_upscale_button(self):
        self.upscale_button = Button(
            style=discord.ButtonStyle.primary,
            label="업스케일링",
            emoji="🔍",
            custom_id=f"upscale_{self.view_id}_{uuid.uuid4().hex[:4]}"  # 고유 ID 사용
        )
        self.upscale_button.callback = self.upscale_callback
        self.add_item(self.upscale_button)

    def remove_upscale_button(self):
        if self.upscale_button and self.upscale_button in self.children:
            self.remove_item(self.upscale_button)

    async def upscale_callback(self, interaction):
        """업스케일링 버튼 클릭 시 호출되는 콜백"""
        await interaction.response.defer(ephemeral=True)
        print("업스케일링 버튼 클릭 시 호출되는 콜백 대기")
        if self.on_upscale_click and self.selected_image_path:
            try:
                print(f"업스케일링 버튼 클릭 시 호출되는 콜백 시작")
                await self.on_upscale_click(interaction, self.selected_image_path)
            except Exception as e:
                print(f"다음 버튼 콜백 함수 호출 중 오류: {str(e)}")
                await interaction.followup.send("업스케일링 진행 중 오류가 발생했습니다.", ephemeral=True)
    #-------------------------------------------------------------------------------------------------------------#
    # 이미지 선택 기능
    #-------------------------------------------------------------------------------------------------------------#
    def add_image_select(self):
        # 이미 선택기가 있으면 추가하지 않음
        for child in self.children:
            if isinstance(child, Select):
                return
                
        self.image_select = Select(
            placeholder="이미지 선택",
            options=[
                discord.SelectOption(label=f"이미지 {i+1}", value=str(i), description=f"이미지 {i+1} 선택") 
                for i in range(self.total_images)
            ],
            custom_id=f"select_{self.view_id}_{uuid.uuid4().hex[:4]}"  # 고유 ID 사용
        )
        self.image_select.callback = self.select_callback
        self.add_item(self.image_select)     

    def remove_image_select(self):
        if self.image_select and self.image_select in self.children:
            self.remove_item(self.image_select)
            
    async def select_callback(self, interaction):
        """이미지 선택 시 호출되는 콜백"""
        if not self.is_multi_image:
            return
        
        # 메시지 ID 저장
        self.message_id = interaction.message.id
        
        # 선택한 이미지 인덱스로 업데이트
        selected_index = int(interaction.data["values"][0])
        
        # 이미지 인덱스 설정 및 콜백 호출
        await self.set_current_image(selected_index)
        
        # 현재 선택된 이미지만 포함하는 파일 생성
        file_path = self.image_paths[f"img_{selected_index}"]
        
        if os.path.exists(file_path):
            try:
                new_file = discord.File(file_path, filename=f"image_{selected_index}.png")
                
                # 먼저 뷰에서 현재 선택기를 제거
                if self.image_select and self.image_select in self.children:
                    self.remove_item(self.image_select)
                    self.image_select = None
                
                # 선택된 이미지 데이터가 있다면 콘텐츠에 추가 정보 표시
                content = f"이미지 {selected_index+1}/{self.total_images}이 선택되었습니다."
                if self.selected_image_data:
                    content += f"\n선택 정보: {self.selected_image_data}"
                
                # 이미지 메시지 업데이트
                await interaction.response.edit_message(content=content, attachments=[new_file], view=self)
                
                # 버튼들 추가
                # 새 버튼들 추가 전에 기존 버튼들이 있는지 확인하고 모두 제거
                self.clear_items()
                
                # 버튼 추가
                self.add_back_button()
                self.add_next_button()
                self.add_save_button()
                self.remove_retry_button()
                self.add_upscale_button()
                # 변경된 뷰를 적용하기 위해 메시지 다시 업데이트
                try:
                    await interaction.edit_original_response(view=self)
                except Exception as e:
                    print(f"뷰 업데이트 오류: {str(e)}")
                    
            except Exception as e:
                print(f"이미지 업데이트 중 오류: {str(e)}")
                # 이미 응답했을 수 있으므로 followup 사용
                try:
                    await interaction.followup.send("이미지 업데이트 중 오류가 발생했습니다.", ephemeral=True)
                except:
                    pass
        else:
            try:
                await interaction.response.send_message("이미지 파일을 찾을 수 없습니다.", ephemeral=True)
            except:
                try:
                    await interaction.followup.send("이미지 파일을 찾을 수 없습니다.", ephemeral=True)
                except:
                    pass
    #-------------------------------------------------------------------------------------------------------------#
    # 이미지 선택 기능
    #-------------------------------------------------------------------------------------------------------------#
    
    #-------------------------------------------------------------------------------------------------------------#
    # 저장 버튼 기능
    #-------------------------------------------------------------------------------------------------------------# 
    def add_save_button(self):
        # 이미 버튼이 있으면 추가하지 않음
        for child in self.children:
            if isinstance(child, Button) and child.custom_id.startswith("save_"):
                return
                
        self.save_button = Button(
            style=discord.ButtonStyle.success,
            label="저장",
            emoji="💾",
            custom_id=f"save_{self.view_id}_{uuid.uuid4().hex[:4]}"  # 고유 ID 사용
        )
        self.save_button.callback = self.save_callback
        self.add_item(self.save_button)
    
    def remove_save_button(self):
        if self.save_button and self.save_button in self.children:
            self.remove_item(self.save_button)
    
    async def save_callback(self, interaction):
        """저장 버튼 클릭 시 호출되는 콜백"""
        await interaction.response.defer(ephemeral=True)
        # 사용자 DM으로 이미지 전송
        try:
            dm_channel = await interaction.user.create_dm()
            # 임시 파일 경로에서 새 discord.File 객체 생성
            image_key = f"img_{self.current_image_index}"
            file_path = self.image_paths[image_key]
            
            if os.path.exists(file_path):
                save_file = discord.File(file_path)
                msg = "요청하신 이미지입니다:"
                if self.is_multi_image:
                    msg = f"요청하신 이미지입니다 (이미지 {self.current_image_index+1}/{self.total_images}):"
                await dm_channel.send(msg, file=save_file)
                await interaction.followup.send("이미지가 DM으로 전송되었습니다!", ephemeral=True)
            else:
                await interaction.followup.send("이미지 파일을 찾을 수 없습니다.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"이미지 저장 중 오류 발생: {str(e)}", ephemeral=True)
    #-------------------------------------------------------------------------------------------------------------#
    # 저장 버튼 기능
    #-------------------------------------------------------------------------------------------------------------#