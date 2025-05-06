# Image Generators Patch Notes

## 주요 변경사항

### 1. StoryBoardGenerator 클래스 워크플로우 파일 이름 변경 (339-341줄)
```python
def __init__(self, server_ip):
    super().__init__(server_ip, "storyboard-maker.json")
    self.timeout = 300  # 스토리보드 생성 프로세스의 타임아웃 설정
```

### 2. prepare_prompt 함수 수정 - JsonParserNode 사용 (343-349줄)
```python
def prepare_prompt(self, prompt, params, seed_value):
    """스토리보드 워크플로우 프롬프트 준비"""
    # 노드별 파라미터 설정
    for node_id, node in prompt.items():
        # 텍스트 인코딩
        if node.get("class_type") == "JsonParserNode" and node.get("_meta", {}).get("title") == "JsonParserNode":
            node["inputs"]["file_name"] = params["prompt_file_name"]
```