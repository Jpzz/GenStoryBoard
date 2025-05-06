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

# 이 파일은 GitHub API 제한으로 인해 간략화되었습니다.
# 실제 파일은 로컬 저장소에서 확인하세요.
# 주요 기능:
# - 이미지 생성 진행률 업데이트
# - 워크플로우 파일 로드
# - 워크플로우 결과 이미지 처리
# - 이미지 및 텍스트 업로드
# - 캐릭터 생성 처리
# - 멀티뷰 캐릭터 생성
# - 스토리보드 생성
# - 텍스트-이미지 변환
# - 이미지-이미지 변환
# - ComfyUI 프롬프트 큐 관리