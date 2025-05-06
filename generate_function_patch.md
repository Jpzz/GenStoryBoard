# Generate Function Patch Notes

## 주요 변경사항

### 1. check_server_setting 함수 개선 (92-120줄)
```python
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
```

### 2. storyboard_process_generate_command 함수 구현 (797-867줄)
```python
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
```