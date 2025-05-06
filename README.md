# GenStoryBoard

스토리보드 생성 및 이미지 생성 자동화 프로젝트

## 주요 기능
- 프롬프트 생성
- 이미지 생성
- ComfyUI 워크플로우 관리

## 디렉토리 구조
- `_comfyui_workflows`: ComfyUI 워크플로우 JSON 파일들 (원본)
  - 캐릭터 생성, 스토리보드 생성, 이미지 변환 등 다양한 워크플로우 포함
  - T2I, I2I, 캐릭터 멀티뷰, T-포즈 등 다양한 기능 워크플로우
- `_comfyui_workflows_clean`: 정리된 ComfyUI 워크플로우 및 미리보기 이미지
  - 워크플로우의 정리된 버전과 해당 워크플로우의 결과물 미리보기 PNG 파일 포함
- `_comfyui_info`: ComfyUI 설정 및 파라미터 정보
  - 서버 설정, 워크플로우 로직, 출력 비율 등의 정보 포함

## 사용 방법
1. 필요한 패키지 설치: `pip install -r requirements.txt`
2. 환경 변수 설정: `.env` 파일에 필요한 API 키 설정
3. ComfyUI 서버 실행
4. 디스코드 봇 실행