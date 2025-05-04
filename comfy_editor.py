import websocket #NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
import time
import socket
import os

def get_status(ip, port=8000):
    try:
        with urllib.request.urlopen(f"http://{ip}:{port}/queue", timeout=30) as response:
            status_data = json.loads(response.read())
            
            # 상태 데이터를 콘솔에 출력 (디버깅용)
            print(f"ComfyUI 상태: {status_data}")
            
            # 상태 데이터 요약 (디스코드 임베드 길이 제한 문제 해결)
            if status_data:
                # ComfyUI는 'queue_running' 키에 배열을 제공함 - 비어있지 않으면 실행 중
                running_tasks = status_data.get("queue_running", [])
                pending_tasks = status_data.get("queue_pending", [])
                
                summary = {
                    "running": len(running_tasks) > 0,  # 실행 중인 태스크가 있는지 여부
                    "pending": len(pending_tasks),
                    "total_queue_size": len(running_tasks) + len(pending_tasks)
                }
                
                # 실행 중인 작업이 있으면 간단한 정보만 포함
                if summary["running"] and running_tasks:
                    # 구조: [노드 수, 프롬프트 ID, 노드 객체, 클라이언트 정보, 실행된 노드 리스트]
                    if len(running_tasks[0]) >= 3:
                        task_info = running_tasks[0]
                        prompt_id = task_info[1] if len(task_info) > 1 else "unknown"
                        nodes_data = task_info[2] if len(task_info) > 2 else {}
                        executed_nodes = task_info[4] if len(task_info) > 4 else []
                        
                        # 작업 정보 구성
                        summary["running_task_info"] = {
                            "prompt_id": prompt_id,
                            "nodes_executed": len(executed_nodes) if executed_nodes else 0,
                            "progress": {"value": len(executed_nodes) if executed_nodes else 0, "max": len(nodes_data) if nodes_data else 1}
                        }
                
                return summary
            return status_data
    except Exception as e:
        print(f"상태 가져오기 실패: {str(e)}")
        return None

def get_view_text(ip, filename, encoding="utf-8"):
    """텍스트 파일을 가져와 문자열로 반환합니다.
    
    Args:
        filename (str): 가져올 텍스트 파일의 이름
        subfolder (str, optional): 텍스트 파일이 있는 하위 폴더. 기본값은 ""
        folder_type (str, optional): 폴더 유형 ("output", "input", "temp"). 기본값은 "output"
        encoding (str, optional): 텍스트 파일의 인코딩. 기본값은 "utf-8"
        
    Returns:
        str 또는 None: 성공하면 텍스트 내용, 실패하면 None
    """
    data = {"filename": filename, "subfolder": "Prompt", "type": "output"}
    url_values = urllib.parse.urlencode(data)
    try:
        with urllib.request.urlopen(f"http://{ip}:{8000}/view?{url_values}", timeout=30) as response:
            binary_data = response.read()
            if binary_data:
                text = binary_data.decode(encoding)
                # 모든 종류의 줄바꿈 문자 처리 (Windows의 \r\n, Unix의 \n, 옛 Mac의 \r)
                text = text.replace('\r\n', ', ').replace('\n', ', ').replace('\r', ', ')
                text = text.replace(".", ",")
                if text and not text.endswith("."):
                    text += "."
                return text
            return None
    except UnicodeDecodeError as e:
        print(f"텍스트 디코딩 실패: {str(e)}. 인코딩이 올바른지 확인하세요.")
        return None
    except Exception as e:
        print(f"텍스트 파일 가져오기 실패: {str(e)}")
        return None

class comfyui_web:
    def __init__(self, ip, port=8000):
        self.client_id = str(uuid.uuid4())
        self.prompt = None
        self.ip = ip
        self.port = port
        self.ws = None  # 웹소켓 연결은 필요할 때 초기화됨
        self.websocket_node_id = None  # SaveImageWebsocket 노드의 ID를 저장
        self.progress_callback = None  # 진행률 업데이트 콜백 함수

    def set_progress_callback(self, callback_fn):
        """
        진행률 업데이트를 위한 콜백 함수를 설정합니다
        
        Args:
            callback_fn: 진행률이 업데이트될 때 호출될 함수(value, max_value) 형식
        """
        self.progress_callback = callback_fn

    def queue_prompt(self):
        if self.prompt is None:
            print("오류: 프롬프트가 설정되지 않았습니다")
            return {"error": "프롬프트가 설정되지 않았습니다"}
            
        p = {"prompt": self.prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        
        try:
            req = urllib.request.Request(f"http://{self.ip}:{self.port}/prompt", data=data)
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read())
        except urllib.error.URLError as e:
            print(f"서버 연결 실패: {str(e)}")
            return {"error": f"서버 연결 실패: {str(e)}"}
        except Exception as e:
            print(f"프롬프트 큐잉 실패: {str(e)}")
            return {"error": f"프롬프트 큐잉 실패: {str(e)}"}
    
    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        try:
            with urllib.request.urlopen(f"http://{self.ip}:{self.port}/view?{url_values}", timeout=30) as response:
                return response.read()
        except Exception as e:
            print(f"이미지 가져오기 실패: {str(e)}")
            return None


    def get_history(self, prompt_id):
        try:
            with urllib.request.urlopen(f"http://{self.ip}:{self.port}/history/{prompt_id}", timeout=30) as response:
                return json.loads(response.read())
        except Exception as e:
            print(f"히스토리 가져오기 실패: {str(e)}")
            return {}

        
    def _find_websocket_node_id(self):
        """워크플로우에서 SaveImageWebsocket 노드의 ID를 찾습니다"""
        if not isinstance(self.prompt, dict):
            return None
            
        # 워크플로우에서 SaveImageWebsocket 노드 찾기
        for node_id, node in self.prompt.items():
            if isinstance(node, dict) and node.get("class_type") == "SaveImageWebsocket":
                print(f"워크플로우에서 SaveImageWebsocket 노드를 찾았습니다: ID={node_id}")
                return node_id
                
        print("워크플로우에서 SaveImageWebsocket 노드를 찾을 수 없습니다")
        return None

    def get_images_from_history(self, prompt_id):
        """히스토리 API를 통해 이미지를 가져옵니다."""
        try:
            history = self.get_history(prompt_id)
            if prompt_id not in history:
                print(f"프롬프트 ID {prompt_id}가 히스토리에 없습니다")
                return None
                
            output_images = {}
            history_data = history[prompt_id]
            
            if 'outputs' in history_data:
                for node_id, output in history_data['outputs'].items():
                    if 'images' in output:
                        images_output = []
                        for image_info in output['images']:
                            print(f"히스토리에서 이미지 찾음: {image_info['filename']}")
                            image_data = self.get_image(
                                image_info['filename'], 
                                image_info['subfolder'], 
                                image_info['type']
                            )
                            if image_data:
                                images_output.append(image_data)
                        
                        if images_output:
                            output_images[node_id] = images_output
            
            if output_images:
                print(f"히스토리 API에서 {sum(len(imgs) for imgs in output_images.values())}개의 이미지를 가져왔습니다")
                return output_images
            else:
                print("히스토리에서 이미지를 찾을 수 없습니다")
                return None
        except Exception as e:
            print(f"히스토리에서 이미지 가져오기 실패: {str(e)}")
            return None

    def _connect_websocket(self):
        """웹소켓 연결을 시도하고 성공 여부를 반환합니다"""
        if self.ws is not None:
            try:
                # 기존 연결 확인 (간단한 핑으로 연결 상태 체크)
                self.ws.ping()
                print("기존 웹소켓 연결이 활성화되어 있습니다")
                return True  # 연결 활성화 상태
            except:
                # 연결이 끊어졌으면 닫아줌
                try:
                    self.ws.close()
                except:
                    pass
                self.ws = None
                print("기존 웹소켓 연결이 끊어져 있어 재연결을 시도합니다")
        
        # 새 연결 시도
        try:
            print(f"웹소켓 연결 시도: ws://{self.ip}:{self.port}/ws?clientId={self.client_id}")
            self.ws = websocket.WebSocket()
            # 초기 연결 시에만 짧은 타임아웃 설정 (연결 실패를 빠르게 감지하기 위함)
            self.ws.connect(f"ws://{self.ip}:{self.port}/ws?clientId={self.client_id}", timeout=10)
            print("웹소켓 연결 성공!")
            return True
        except (socket.timeout, ConnectionRefusedError, websocket.WebSocketException) as e:
            print(f"웹소켓 연결 실패: {str(e)}")
            self.ws = None
            return False
        except Exception as e:
            print(f"웹소켓 연결 중 예상치 못한 오류: {str(e)}")
            self.ws = None
            return False

    def get_images(self, timeout: int):
        """웹소켓을 통해 이미지를 가져옵니다"""
        if not self._connect_websocket():
            print("웹소켓 연결에 실패했습니다. HTTP API를 통한 이미지 가져오기를 시도합니다")
            
        # SaveImageWebsocket 노드 ID 찾기
        if self.websocket_node_id is None:
            self.websocket_node_id = self._find_websocket_node_id()
            if self.websocket_node_id:
                print(f"사용할 SaveImageWebsocket 노드 ID: {self.websocket_node_id}")
            
        # 프롬프트 전송
        prompt_resp = self.queue_prompt()
        if isinstance(prompt_resp, dict) and "error" in prompt_resp:
            return prompt_resp
        
        if not isinstance(prompt_resp, dict) or "prompt_id" not in prompt_resp:
            return {"error": "프롬프트 ID를 받지 못했습니다"}
            
        prompt_id = prompt_resp["prompt_id"]
        print(f"프롬프트 ID: {prompt_id} - 이미지 생성 대기 중...")
        
        # 웹소켓 연결이 성공한 경우에만 웹소켓으로 이미지 수신 시도
        if self.ws is not None:
            try:
                output_images = self._get_images_via_websocket(prompt_id, timeout)
                
                if output_images and any(len(images) > 0 for images in output_images.values()):
                    print(f"웹소켓으로 이미지 수신 성공: {sum(len(images) for images in output_images.values())}개")
                    return output_images
            except Exception as e:
                print(f"웹소켓을 통한 이미지 수신 실패: {str(e)}")
        
        # 웹소켓 수신 실패 시 히스토리 API로 시도
        print("웹소켓으로 이미지를 받지 못했습니다. 히스토리 API를 통해 이미지를 가져옵니다")
        # 이미지 생성 완료를 기다림
        time.sleep(5)  # 서버에서 이미지 처리가 완료될 시간 부여
        
        history_images = self.get_images_from_history(prompt_id)
        if history_images:
            print("히스토리에서 이미지를 성공적으로 가져왔습니다")
            # 이미지 데이터 형식 맞추기
            formatted_images = {}
            for node_id, images in history_images.items():
                formatted_images[node_id] = [{"data": img_data, "type": "temp", "filename": f"history_{i}.png"} 
                                          for i, img_data in enumerate(images)]
            return formatted_images
        
        return {"error": "이미지를 받을 수 없습니다. 서버 연결을 확인해주세요"}

    def _get_images_via_websocket(self, prompt_id, timeout: int = 180):
        """웹소켓을 통해 이미지를 수신합니다"""
        output_images = {}
        current_node = ""
        total_steps = 0
        current_step = 0
        
        print(f"웹소켓을 통한 이미지 수신 시작 (프롬프트 ID: {prompt_id})")
        
        try:
            # 시간 제한 설정
            max_wait_time = timeout  # 초
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    # 타임아웃 설정 (10초마다 연결 상태 확인)
                    self.ws.settimeout(10)
                    out = self.ws.recv()
                    
                    if isinstance(out, str):
                        message = json.loads(out)
                        
                        # 웹소켓 메시지 타입 로깅
                        print(f"웹소켓 메시지 수신: {message['type']}")
                        
                        if message['type'] == 'executing':
                            data = message['data']
                            if data['prompt_id'] == prompt_id:
                                if data['node'] is None:
                                    print("모든 노드 실행 완료")
                                    break  # 실행 완료
                                else:
                                    current_node = data['node']
                                    print(f"노드 실행 중: {current_node}")
                        elif message['type'] == 'progress':
                            data = message['data']
                            current_step = data['value']
                            total_steps = data['max']
                            print(f"진행률: {current_step}/{total_steps}")
                            
                            # 진행률 콜백 호출
                            if self.progress_callback is not None:
                                try:
                                    self.progress_callback(current_step, total_steps)
                                except Exception as e:
                                    print(f"진행률 콜백 실행 중 오류: {str(e)}")
                        elif message['type'] == 'executed':
                            # 노드 실행 완료 정보
                            if 'node' in message:
                                node_id = message['node']
                                print(f"노드 {node_id} 실행 완료")
                                if 'output' in message:
                                    output = message['output']
                                    if output and isinstance(output, dict):
                                        print(f"노드 {node_id}의 출력 정보: {list(output.keys())}")
                                        if 'images' in output:
                                            print(f"노드 {node_id}의 실행 결과에 이미지가 포함되어 있습니다")
                    else:
                        # 바이너리 데이터 - 이미지
                        # SaveImageWebsocket 클래스 타입을 가진 노드(들)의 ID로 확인
                        if self.websocket_node_id and current_node == self.websocket_node_id:
                            images_output = output_images.get(current_node, [])
                            # 앞 8바이트는 헤더이므로 제외
                            image_data = out[8:]
                            images_output.append({"data": image_data, "type": "temp", "filename": f"websocket_image_{len(images_output)}.png"})
                            output_images[current_node] = images_output
                            print(f"이미지 수신 완료: {len(images_output)}개 (노드 ID: {current_node})")
                    
                except websocket.WebSocketTimeoutException:
                    # 타임아웃이 발생하면 연결 상태 확인
                    try:
                        self.ws.ping()
                        print("웹소켓 연결 유지 중... 이미지 생성 계속 대기 중")
                        continue
                    except:
                        print("웹소켓 연결이 끊어졌습니다")
                        break
            
            # 시간 초과 체크
            if time.time() - start_time >= max_wait_time:
                print(f"최대 대기 시간({max_wait_time}초)이 초과되었습니다")
        
        except Exception as e:
            print(f"웹소켓을 통한 이미지 수신 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return output_images

    def run(self, timeout: int = 180):
        """프롬프트를 실행하고 이미지를 반환합니다"""
        # 워크플로우에서 SaveImageWebsocket 노드 ID 찾기 (있으면 저장)
        self.websocket_node_id = self._find_websocket_node_id()
        
        # 프롬프트에 SaveImageWebsocket 노드가 있는지 확인하고 없으면 추가
        if self.prompt and isinstance(self.prompt, dict) and not self.websocket_node_id:
            print("SaveImageWebsocket 노드 추가 중...")
            last_image_node = None
            
            # 이미지를 출력하는 마지막 노드 찾기
            for node_id, node in self.prompt.items():
                if isinstance(node, dict) and "class_type" in node and node["class_type"] in ["VAEDecode", "SaveImage"]:
                    last_image_node = node_id
            
            if last_image_node:
                # SaveImageWebsocket 노드 ID 생성 (기존 워크플로우와 충돌하지 않는 값)
                new_node_id = "websocket_node"
                
                # 같은 ID가 있는지 확인하고, 있으면 다른 ID 사용
                if new_node_id in self.prompt:
                    # 숫자 ID 중 가장 큰 값 + 1 사용
                    numeric_ids = [int(id) for id in self.prompt.keys() if id.isdigit()]
                    if numeric_ids:
                        new_node_id = str(max(numeric_ids) + 1)
                    else:
                        new_node_id = "999"  # 임의의 큰 숫자
                
                # SaveImageWebsocket 노드 추가
                self.prompt[new_node_id] = {
                    "class_type": "SaveImageWebsocket",
                    "inputs": {
                        "images": [
                            last_image_node,
                            0  # 첫 번째 출력 인덱스
                        ]
                    }
                }
                self.websocket_node_id = new_node_id  # 추가한 노드 ID 저장
                print(f"SaveImageWebsocket 노드(ID: {new_node_id})가 {last_image_node} 노드에 연결되었습니다")
            else:
                print("경고: SaveImageWebsocket을 연결할 적절한 노드를 찾을 수 없습니다")
        
        # 이미지 가져오기
        try:
            # 먼저 웹소켓 연결 시도
            connected = self._connect_websocket()
            if not connected:
                print("웹소켓 연결 실패 - HTTP API를 통해 이미지를 가져옵니다")
            
            # 타임아웃 값 디버깅
            print(f"이미지 생성 타임아웃: {timeout}초")
            
            # 이미지 수신
            return self.get_images(timeout)
            
        except Exception as e:
            print(f"실행 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"실행 중 오류: {str(e)}"}
        finally:
            # 항상 웹소켓 연결을 정리
            self.close()

    def select_prompt(self, prompt):
        """
        사용할 프롬프트를 선택합니다
        
        Args:
            prompt: 이미지 생성에 사용할 프롬프트
            
        Returns:
            선택된 프롬프트
        """
        self.prompt = prompt
        # 프롬프트가 설정되면 SaveImageWebsocket 노드 ID 초기화
        self.websocket_node_id = None
        return self.prompt
        
    def close(self):
        """웹소켓 연결이 열려있으면 닫습니다"""
        if self.ws is not None:
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
            print("웹소켓 연결 종료")
            
    def __del__(self):
        """객체가 삭제될 때 웹소켓 연결을 닫습니다"""
        self.close()