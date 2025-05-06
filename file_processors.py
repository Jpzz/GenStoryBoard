import pandas as pd
import os, asyncio
from prompt_generator import translate_to_flux_prompt
import json

system_scene_prompt = """
You are Flux model prompt generator. Given Korean text, translate it to English and generate a prompt for Flux model.

# Important
1. Translate Korean text to English.
2. Generate a prompt for Flux model.
3. Not translate character name.
   - Generally, character name is enclosed in "".
   - Example: "소명"
4. Return only the prompt, not additional information.

# Scene Description
1. Given scene description in Korean, translate it to English.
2. Given negative in Korean, translate it to English.
3. Negative translation example: 
    - Korean: 못생김
    - English: not ugly
4. Mixed scene description and negative to one prompt.

# Time and Weather
1. Given time and weather in Korean, translate it to English.
2. Return only the time and weather, not additional information.

# Camera Shot
1. Given camera shot in Korean, translate it to English.
2. Return only the camera shot, not additional information.

# Composition
1. Given composition in Korean, translate it to English.
2. Given composition details in Korean, translate it to English.
3. Mixed composition and composition details to one prompt.

# Ouput (JSON Format Style)
{
    "scene_description": "Scene description",
    "time_and_weather": "Time and weather",
    "camera_shot": "Camera shot",
    "composition": "Composition",
}
"""
system_char_prompt = """
You are Flux model prompt generator. Given Korean text, translate it to English and generate a prompt for Flux model.

# Important
1. Translate Korean text to English.
2. Generate a prompt for Flux model.
3. Return only the prompt as translation result, not additional information.

# Main Character Korean Name
1. Given main character name in Korean, use it as it is.

# Main Character English Name
1. Given main character name in English, use it as it is.

# Main Character Description
1. Given main character description in Korean, translate it to English.

# Sub Character Korean Name
1. Given sub character name in Korean, use it as it is.

# Sub Character English Name
1. Given sub character name in English, use it as it is.

# Sub Character Description
1. Given sub character description in Korean, translate it to English.

# Ouput (JSON Format Style)
{
    "main_char_ko_name": "Main Character Korean Name",
    "main_char_en_name": "Main Character English Name",
    "main_char_description": "Main Character Description",
    "sub_char_ko_name": "Sub Character Korean Name",
    "sub_char_en_name": "Sub Character English Name",
    "sub_char_description": "Sub Character Description"
}
"""
#----------------------------------------------------------------------------------------------#
# CSV or Excel 파일 처리
#----------------------------------------------------------------------------------------------#
def process_csv(file_path):
    """
    Load a CSV or Excel file and return the first column as a list.
    
    Args:
        file_path (str): Path to the CSV or Excel file
        column_index (int, optional): Index of the column to extract. Defaults to 0.
        
    Returns:
        list: First column of the file
    """
    if (file_path.endswith(".csv")):
        df = pd.read_csv(file_path)
    elif (file_path.endswith(".xlsx")):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Only CSV and XLSX files are supported.")
    
    scene_info = []
    for i in range(1, len(df)):
        scene_info.append(df.iloc[i, 0:7].tolist())
    
    character_info = df.iloc[:3, 7].tolist()
    sub_character_info = df.iloc[:3, 8].tolist()
    
    return scene_info, character_info, sub_character_info
#----------------------------------------------------------------------------------------------#
# CSV or Excel 파일 처리
#----------------------------------------------------------------------------------------------#

#----------------------------------------------------------------------------------------------#
# 텍스트 파일 처리
#----------------------------------------------------------------------------------------------#
async def process_txt(file_path, file_name, row=1):
    scene, character_info, sub_character_info = process_csv(file_path)
    
    tasks = []
    for idx, row in enumerate(scene):
        user_scene_prompt = f"""
        "Scene description": {row[0]}
        "Time and weather": {row[1]}
        "Camera shot": {row[2]}
        "Composition": {row[4]}
        "Composition Details": {row[5]}
        "Negative": {row[6]}
        """
        tasks.append(translate_to_flux_prompt(system_scene_prompt, user_scene_prompt))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)

    user_char_prompt = f"""
    "Main Character Korean Name": {character_info[0]}
    "Main Character English Name": {character_info[1]}
    "Main Character Description": {character_info[2]}
    "Sub Character Korean Name": {sub_character_info[0]}
    "Sub Character English Name": {sub_character_info[1]}
    "Sub Character Description": {sub_character_info[2]}
    """
    character_results = await translate_to_flux_prompt(system_char_prompt, user_char_prompt)
    print(f"예시로 : {results[0]}\n{character_results}")

    scene_prompt_dict = {}
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error processing row {idx}: {result}")
            prompt = "Error processing prompt"
        else:
            if result:
                # result 파일 json 로드
                try:
                    json_result = json.loads(result)
                except json.JSONDecodeError:
                    print(f"Error parsing JSON for row {idx}")
                    json_result = {"error": "JSON parsing error"}
                scene_prompt_dict[idx] = json_result

    # character result 파일 json 로드
    try:
        char_json_result = json.loads(character_results)
    except json.JSONDecodeError:
        print(f"Error parsing JSON for character results")
        char_json_result = {"error": "JSON parsing error"}
    
    final_dict = {}
    final_dict["scene"] = scene_prompt_dict
    final_dict["character"] = char_json_result
    
    json_path = os.path.join(os.path.dirname(__file__), "_storyboard", "_prompt", f"{file_name}")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(final_dict, ensure_ascii=False, indent=4, sort_keys=True))
    return json_path
#----------------------------------------------------------------------------------------------#
# 텍스트 파일 처리
#----------------------------------------------------------------------------------------------#

if __name__ == "__main__":
    asyncio.run(process_txt("_storyboard/CoffeeBreak.xlsx", "vilab_jungho kim_833080")) 