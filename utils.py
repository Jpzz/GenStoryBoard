import json
import os
import discord
import random

def initialize_server_list():
    with open(os.path.join(os.path.dirname(__file__),'_comfyui_info', 'comfyui_server.json'), 'r') as f:
        server_list = json.load(f)
    return server_list

def set_embed(msg_title :str, msg_description :str, msg_color):
    embed = discord.Embed(
        title = msg_title,
        description = msg_description,
        color = msg_color
    )
    return embed

def load_workflow_parameter():
    with open(os.path.join(os.path.dirname(__file__),'_comfyui_info', 'comfyui_workflow_parameter.json'), 'r') as f:
        workflow_parameter = json.load(f)
    return workflow_parameter

def load_workflow_logic():
    with open(os.path.join(os.path.dirname(__file__),'_comfyui_info', 'comfyui_workflow_logic.json'), 'r') as f:
        workflow_logic = json.load(f)
    return workflow_logic

def set_file_name(interaction, ext:str):
    # 사용자 별명 또는 이름 가져오기
    user = interaction.user
    if hasattr(user, 'nick') and user.nick:
        user_name = user.nick
    else:
        user_name = user.name
    unique_id = f"{user_name}"
    unique_num = str(random.randint(1, 999999))
    return f"{unique_id}_{unique_num}.{ext}"
    