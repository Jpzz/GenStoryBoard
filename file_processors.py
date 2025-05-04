import pandas as pd
import os, asyncio
from prompt_generator import translate_to_flux_prompt
import json

test_string = """A mysterious figure named "소명" stealthily infiltrates the advanced power facility in Shin Seoul, surrounded by sleek, reflective metal walls that gleam under pulsating LED lights, intricate hologram displays projecting ethereal data streams, and vigilant security drones equipped with scanning laser sensors patrolling the area. In this cyberpunk-inspired scene, "소명" moves cautiously through the shadows to siphon electricity, emphasizing a tense and atmospheric mood with high-contrast lighting, subtle neon accents, and a dark, immersive palette that highlights the facility's futuristic design. To maintain the stealthy essence, ensure that "소명's" face is dimly lit and not brightly illuminated, avoiding any overexposure that might reveal too much detail, and make sure no other characters appear in the background to keep the focus solely on "소명" and the high-tech environment.

Evening 8 PM, clear weather with a crisp, unobstructed night sky.

Medium shot capturing the scene with balanced framing.

"소명" is positioned on the right side of the frame, with the facility's entrance visible on the left, and "소명" moving carefully from right to left to create a dynamic and directional composition."""

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
    
    row_info = []
    for i in range(1, len(df)):
        row_info.append(df.iloc[i, :].tolist())
    return row_info
#----------------------------------------------------------------------------------------------#
# CSV or Excel 파일 처리
#----------------------------------------------------------------------------------------------#

#----------------------------------------------------------------------------------------------#
# 텍스트 파일 처리
#----------------------------------------------------------------------------------------------#
async def process_txt(file_path, file_name, row=1):
    scene = process_csv(file_path)
    
    tasks = []
    for idx, row in enumerate(scene):
        tasks.append(translate_to_flux_prompt(row))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print(f"예시로 : {results[0]}")

    prompt_dict = {}
    prompt_txt = ""
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error processing row {idx}: {result}")
            prompt = "Error processing prompt"
        else:
            if result:
                dict = {}
                prompt = result.replace(":", "is")
                seperate_prompt = prompt.split("\n")
                dict["scene_description"] = seperate_prompt[0]
                dict["time_and_weather"] = seperate_prompt[2]
                dict["camera_shot"] = seperate_prompt[4]
                dict["composition"] = seperate_prompt[6]
                dict["negative"] = ""
                prompt_dict[idx] = dict
                prompt_txt += f"positive: {prompt.replace(chr(10), '')}\n\nnegative: \n---\n"
            else:
                prompt = "Error processing prompt"

    json_path = os.path.join(os.path.dirname(__file__), "_storyboard", "_prompt", f"{file_name}.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(prompt_dict, ensure_ascii=False, indent=4))
    
    txt_path = os.path.join(os.path.dirname(__file__), "_storyboard", "_prompt", f"{file_name}.txt")
    os.makedirs(os.path.dirname(txt_path), exist_ok=True)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(prompt_txt)
    return json_path, txt_path
#----------------------------------------------------------------------------------------------#
# 텍스트 파일 처리
#----------------------------------------------------------------------------------------------#

if __name__ == "__main__":
    asyncio.run(process_txt("_storyboard/_excel/CoffeeBreak.xlsx", "vilab_jungho kim_833080")) 