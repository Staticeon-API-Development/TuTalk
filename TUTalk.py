import webview
import socket
import threading
import json
import uuid
import time
import os
import shutil # 引入高级文件操作模块用于拷贝
import sys

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ==========================================
# 前端 UI (保持不变)
# ==========================================
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>TUTalk</title>
    <style>
        :root { --bg: #ededed; --primary: #07c160; --bubble-me: #95ec69; --bubble-other: #ffffff; --sidebar-bg: #e6e6e6; }
        body { font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; background: var(--bg); margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        
        #login-screen { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; background: white; z-index: 10; }
        .login-box { width: 300px; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); text-align: center; }
        .login-box input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; }
        .login-box button { width: 100%; padding: 12px; background: var(--primary); color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; transition: 0.2s;}
        .login-box button:hover { background: #06ad56; }

        #main-container { display: none; flex: 1; height: 100%; }
        
        #sidebar { width: 220px; background: var(--sidebar-bg); border-right: 1px solid #ddd; display: flex; flex-direction: column; }
        .sidebar-header { padding: 15px; background: #dbdbdb; font-weight: bold; border-bottom: 1px solid #ccc; font-size: 14px; }
        #peer-list { list-style: none; margin: 0; padding: 0; overflow-y: auto; flex: 1; }
        .peer-item { padding: 12px 15px; border-bottom: 1px solid #e0e0e0; display: flex; flex-direction: column; font-size: 14px; }
        .peer-item .peer-name { font-weight: bold; color: #333; margin-bottom: 4px; }
        .peer-item .peer-ip { font-size: 11px; color: #888; }
        
        #chat-screen { flex: 1; display: flex; flex-direction: column; height: 100%; }
        #header { padding: 15px; background: #f5f5f5; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center;}
        
        #chat-area { flex: 1; overflow-y: auto; padding: 20px; }
        
        .msg-row { display: flex; margin-bottom: 20px; width: 100%; flex-direction: column; }
        .msg-row.me { align-items: flex-end; }
        .msg-row.other { align-items: flex-start; }
        .msg-row.system { align-items: center; margin-bottom: 10px; }
        
        .meta { font-size: 12px; color: #888; margin-bottom: 4px; padding: 0 5px; }
        .bubble { max-width: 75%; padding: 10px 14px; border-radius: 8px; font-size: 15px; line-height: 1.5; word-wrap: break-word; box-shadow: 0 1px 3px rgba(0,0,0,0.05); white-space: pre-wrap; }
        .me .bubble { background-color: var(--bubble-me); border-top-right-radius: 2px; }
        .other .bubble { background-color: var(--bubble-other); border-top-left-radius: 2px; }
        .system .bubble { background-color: rgba(0,0,0,0.1); color: #555; font-size: 12px; padding: 4px 10px; border-radius: 12px; box-shadow: none; }
        
        .file-card { border: 1px solid #ddd; padding: 15px; border-radius: 6px; background: #fafafa; text-align: center; color: #333; min-width: 200px;}
        .file-card b { display: block; margin-bottom: 5px; word-break: break-all; }
        .file-card span { font-size: 12px; color: #888; }
        .file-card button { margin-top: 10px; padding: 6px 15px; background: white; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; transition: 0.2s; }
        .file-card button:hover { background: #eee; }

        #input-area { display: flex; padding: 15px; background: #f5f5f5; border-top: 1px solid #ddd; align-items: flex-end;}
        textarea { flex: 1; height: 60px; min-height: 60px; max-height: 150px; resize: none; border: 1px solid #ccc; border-radius: 6px; padding: 10px; font-family: inherit; font-size: 14px; outline: none; }
        textarea:focus { border-color: var(--primary); }
        .tool-btn { margin-left: 10px; padding: 0 15px; height: 45px; background: white; color: #333; border: 1px solid #ccc; border-radius: 6px; cursor: pointer; font-size: 18px;}
        .tool-btn:hover { background: #eee; }
        .send-btn { margin-left: 10px; padding: 0 25px; height: 45px; background: var(--primary); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>

    <div id="login-screen">
        <div class="login-box">
            <h2 style="margin-top:0;">欢迎使用 TUTalk</h2>
            <input type="number" id="port-input" value="50000" placeholder="广播频道 (1024-65535)">
            <input type="text" id="name-input" placeholder="你的昵称">
            <button onclick="joinChannel()">启动网络</button>
        </div>
    </div>

    <div id="main-container">
        <div id="sidebar">
            <div class="sidebar-header">在线用户 (<span id="online-count">1</span>)</div>
            <ul id="peer-list"></ul>
        </div>
        
        <div id="chat-screen">
            <div id="header">
                <b id="header-title">TUTalk 频道: 50000</b>
                <button onclick="requestSync()" style="padding:5px 10px; cursor:pointer;">🔄 随机同步历史</button>
            </div>
            <div id="chat-area"></div>
            <div id="input-area">
                <textarea id="msg-input" placeholder="输入消息 (Enter 发送, Shift+Enter 换行)"></textarea>
                <button class="tool-btn" onclick="selectFile()" title="发送安全文件 (上限 1024MB)">📁</button>
                <button class="send-btn" onclick="sendMsg()">发送</button>
            </div>
        </div>
    </div>

    <script>
        function escapeHTML(text) {
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\\n/g, "<br>");
        }

        let myUid = "";
        let myName = "";

        function joinChannel() {
            const port = document.getElementById('port-input').value;
            let name = document.getElementById('name-input').value.trim();
            if(!name) name = "匿名用户";
            myName = name;

            pywebview.api.login(parseInt(port), name).then(res => {
                if(res.success) {
                    myUid = res.uid;
                    document.getElementById('login-screen').style.display = 'none';
                    document.getElementById('main-container').style.display = 'flex';
                    document.getElementById('header-title').innerText = `频道: ${port} | IP: ${res.ip}`;
                    renderSystemMsg("✅ 轻量级无状态网络已启动，支持文件共享");
                    updateOnlineList([]); 
                } else {
                    alert("启动失败: " + res.error);
                }
            });
        }

        function renderSystemMsg(text) {
            const chat = document.getElementById('chat-area');
            const row = document.createElement('div');
            row.className = 'msg-row system';
            row.innerHTML = `<div class="bubble">${text}</div>`;
            chat.appendChild(row);
            chat.scrollTop = chat.scrollHeight;
        }

        function renderMessage(msg) {
            const chat = document.getElementById('chat-area');
            if(document.getElementById(msg.id)) return; 
            
            const isMe = (msg.uid === myUid);
            const row = document.createElement('div');
            row.className = 'msg-row ' + (isMe ? 'me' : 'other');
            row.id = msg.id;
            
            const date = new Date(msg.time * 1000);
            const timeStr = date.toLocaleTimeString('zh-CN', {hour12: false});
            const syncMark = msg.is_sync ? " (历史)" : "";
            
            let bubbleContent = "";
            if (msg.msg_type === "file") {
                const mb = (msg.file_size / (1024 * 1024)).toFixed(2);
                bubbleContent = `
                    <div class="file-card">
                        <b>📁 ${escapeHTML(msg.filename)}</b>
                        <span>大小: ${mb} MB</span><br>
                        <button onclick="downloadFile('${msg.ip}', ${msg.tcp_port}, '${msg.file_id}', '${escapeHTML(msg.filename)}')">
                            ⬇️ 下载文件
                        </button>
                    </div>
                `;
            } else {
                bubbleContent = escapeHTML(msg.text);
            }
            
            row.innerHTML = `
                <div class="meta">${timeStr} - ${msg.sender} [${msg.ip}] ${syncMark}</div>
                <div class="bubble">${bubbleContent}</div>
            `;
            
            chat.appendChild(row);
            chat.scrollTop = chat.scrollHeight;
        }

        function sendMsg() {
            const input = document.getElementById('msg-input');
            const text = input.value.trim();
            if(!text) return;
            pywebview.api.send_message(text).then(() => {
                input.value = '';
                input.focus();
            });
        }

        function selectFile() {
            pywebview.api.select_and_send_file();
        }

        function downloadFile(ip, port, fileId, filename) {
            renderSystemMsg(`⏳ 正在请求下载: ${filename}...`);
            pywebview.api.download_file(ip, port, fileId, filename);
        }

        function requestSync() {
            pywebview.api.request_sync();
        }

        function updateOnlineList(peers) {
            const list = document.getElementById('peer-list');
            list.innerHTML = `
                <li class="peer-item" style="background: #f0f0f0;">
                    <span class="peer-name">${myName} (我)</span>
                    <span class="peer-ip">IP: 本机</span>
                </li>
            `;
            peers.forEach(p => {
                list.innerHTML += `
                    <li class="peer-item">
                        <span class="peer-name">🟢 ${p.name}</span>
                        <span class="peer-ip">${p.ip}</span>
                    </li>
                `;
            });
            document.getElementById('online-count').innerText = peers.length + 1;
        }

        document.getElementById('msg-input').addEventListener('keydown', function(e) {
            if(e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMsg();
            }
        });
    </script>
</body>
</html>
"""

# ==========================================
# 后端 (引入缓存防篡改机制 + 1024MB 限制)
# ==========================================
class ChatAPI:
    def __init__(self):
        self.window = None 
        self.uid = uuid.uuid4().hex
        self.local_ip = get_local_ip()
        
        self.history = {}
        self.online_peers = {} 
        self.peer_lock = threading.Lock() 
        
        # 创建缓存文件夹，防止源文件被篡改或删除
        self.cache_dir = os.path.join(os.getcwd(), "TUTalk_Cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 记录被缓存好的文件：{ file_id: "缓存文件夹下的绝对路径" }
        self.hosted_files = {}
        
        self.udp_sock = None
        self.tcp_server = None
        self.udp_port = 0
        self.tcp_port = 0
        self.name = ""

    def login(self, udp_port, name):
        self.udp_port = udp_port
        self.name = name
        
        try:
            self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_server.bind(("", 0))
            self.tcp_server.listen(10)
            self.tcp_port = self.tcp_server.getsockname()[1] 

            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65535)
            self.udp_sock.bind(("", self.udp_port))
            
            threading.Thread(target=self._heartbeat_sender, daemon=True).start()
            threading.Thread(target=self._udp_listener, daemon=True).start()
            threading.Thread(target=self._tcp_server_loop, daemon=True).start()
            threading.Thread(target=self._peer_cleaner, daemon=True).start()
            
            return {"success": True, "ip": self.local_ip, "uid": self.uid, "tcp_port": self.tcp_port}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- UDP 心跳与监听层 (缩略) ---
    def _heartbeat_sender(self):
        while True:
            hb_msg = {"type": "heartbeat", "uid": self.uid, "name": self.name, "tcp_port": self.tcp_port}
            self._udp_broadcast(hb_msg)
            time.sleep(3)

    def _peer_cleaner(self):
        while True:
            time.sleep(5)
            now = time.time()
            offline_uids = []
            with self.peer_lock:
                for uid, p in self.online_peers.items():
                    if now - p["last_seen"] > 10: offline_uids.append(uid)
                for uid in offline_uids:
                    name = self.online_peers[uid]["name"]
                    del self.online_peers[uid]
                    self._ui_system_msg(f"❌ 节点 [{name}] 已离线")
            if offline_uids: self._notify_ui_peers()

    def _udp_listener(self):
        while True:
            try:
                data, addr = self.udp_sock.recvfrom(65535)
                msg = json.loads(data.decode('utf-8'))
                pkt_type = msg.get("type")
                if pkt_type == "heartbeat":
                    peer_uid = msg.get("uid")
                    if peer_uid != self.uid:
                        with self.peer_lock:
                            is_new = peer_uid not in self.online_peers
                            self.online_peers[peer_uid] = {
                                "name": msg["name"], "ip": addr[0], 
                                "tcp_port": msg["tcp_port"], "last_seen": time.time()
                            }
                        if is_new:
                            self._ui_system_msg(f"✅ 节点 [{msg['name']}] 已上线")
                            self._notify_ui_peers()
                elif pkt_type == "chat":
                    msg_data = msg.get("data")
                    msg_id = msg_data.get("id")
                    if msg_id not in self.history:
                        self.history[msg_id] = msg_data
                        self._ui_render_msg(msg_data)
            except Exception:
                pass

    def _udp_broadcast(self, data_dict):
        try:
            payload = json.dumps(data_dict).encode('utf-8')
            self.udp_sock.sendto(payload, ('255.255.255.255', self.udp_port))
        except Exception:
            pass

    # --- TCP 路由处理层 ---
    def _tcp_server_loop(self):
        while True:
            try:
                client_sock, addr = self.tcp_server.accept()
                threading.Thread(target=self._handle_tcp_request, args=(client_sock,), daemon=True).start()
            except Exception:
                pass

    def _handle_tcp_request(self, sock):
        try:
            f = sock.makefile('rb')
            cmd_line = f.readline().decode('utf-8').strip()
            if not cmd_line: return
            
            req = json.loads(cmd_line)
            action = req.get("cmd")

            if action == "sync":
                payload = json.dumps(list(self.history.values())).encode('utf-8')
                sock.sendall(payload)
                
            elif action == "download":
                file_id = req.get("file_id")
                filepath = self.hosted_files.get(file_id)
                
                # 从 TUTalk_Cache 中安全读取文件供别人下载
                if filepath and os.path.exists(filepath):
                    with open(filepath, 'rb') as file:
                        while chunk := file.read(65536):
                            sock.sendall(chunk)
                else:
                    print("请求的缓存文件不存在")
                    
        except Exception as e:
            print(f"TCP 处理错误: {e}")
        finally:
            sock.close()

    # --- 核心业务 API (被 JS 调用) ---

    def send_message(self, text):
        msg_data = {
            "id": uuid.uuid4().hex, "uid": self.uid, "ip": self.local_ip, "sender": self.name,
            "msg_type": "text", "text": text, "time": time.time()
        }
        self.history[msg_data["id"]] = msg_data 
        self._ui_render_msg(msg_data)           
        self._udp_broadcast({"type": "chat", "data": msg_data}) 

    def select_and_send_file(self):
        if not self.window: return
        file_paths = self.window.create_file_dialog(webview.OPEN_DIALOG)
        if not file_paths: return
        
        filepath = file_paths[0]
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        
        # 1. 安全限制：文件最大不允许超过 1024 MB (1GB)
        MAX_SIZE = 1024 * 1024 * 1024
        if filesize > MAX_SIZE:
            self._ui_system_msg(f"⚠️ 文件 [{filename}] 超过 1024MB 的体积限制，拒绝发送！")
            return
            
        # 2. 避免界面卡死：把大文件的拷贝操作交给后台线程处理
        self._ui_system_msg(f"⏳ 正在将 [{filename}] 拷贝至安全缓存区，请稍候...")
        threading.Thread(target=self._cache_and_broadcast_file, args=(filepath, filename, filesize), daemon=True).start()

    def _cache_and_broadcast_file(self, original_path, filename, filesize):
        """后台线程：将文件拷贝到缓存目录，然后再向全网广播发送"""
        try:
            file_id = uuid.uuid4().hex
            # 为了防止同名文件冲突，在缓存的文件名前加上 file_id 前缀
            cached_filename = f"{file_id}_{filename}"
            cached_path = os.path.join(self.cache_dir, cached_filename)
            
            # 拷贝文件 (此时如果原文件被修改，只会影响拷贝出来的这一份，网络上的这一份已经锁死了)
            shutil.copy2(original_path, cached_path)
            
            # 记录的不再是原文件路径，而是缓存的安全路径
            self.hosted_files[file_id] = cached_path
            
            msg_data = {
                "id": uuid.uuid4().hex,
                "uid": self.uid, "ip": self.local_ip, "sender": self.name,
                "msg_type": "file",
                "file_id": file_id,
                "filename": filename,
                "file_size": filesize,
                "tcp_port": self.tcp_port,
                "time": time.time()
            }
            
            self.history[msg_data["id"]] = msg_data 
            self._ui_render_msg(msg_data)           
            self._udp_broadcast({"type": "chat", "data": msg_data})
            
            self._ui_system_msg(f"✅ 文件 [{filename}] 缓存完毕，现已允许群员下载。")
            
        except Exception as e:
            self._ui_system_msg(f"❌ 文件缓存失败，无法发送: {e}")

    def download_file(self, ip, port, file_id, default_filename):
        if not self.window: return
        if ip == self.local_ip and port == self.tcp_port:
            self._ui_system_msg(f"⚠️ 文件 [{default_filename}] 就是你发出的。")
            return

        save_paths = self.window.create_file_dialog(webview.SAVE_DIALOG, save_filename=default_filename)
        if not save_paths: return
        save_path = save_paths[0]

        threading.Thread(target=self._do_download, args=(ip, port, file_id, save_path, default_filename), daemon=True).start()

    def _do_download(self, ip, port, file_id, save_path, filename):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            
            req = {"cmd": "download", "file_id": file_id}
            sock.sendall((json.dumps(req) + "\n").encode('utf-8'))
            
            with open(save_path, 'wb') as f:
                while True:
                    chunk = sock.recv(65536)
                    if not chunk: break
                    f.write(chunk)
            
            sock.close()
            self._ui_system_msg(f"✅ 文件 [{filename}] 下载成功！")
        except Exception as e:
            self._ui_system_msg(f"❌ 文件下载失败: {e}")

    def request_sync(self):
        with self.peer_lock:
            if not self.online_peers:
                self._ui_system_msg("⚠️ 局域网内没有其他在线节点，无法同步。")
                return
            peer = next(iter(self.online_peers.values()))
            
        self._ui_system_msg(f"🔄 正在通过短连接向 [{peer['name']}] 拉取全量历史数据...")
        threading.Thread(target=self._fetch_history_from_peer, args=(peer,), daemon=True).start()

    def _fetch_history_from_peer(self, peer):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((peer['ip'], peer['tcp_port']))
            
            req = {"cmd": "sync"}
            sock.sendall((json.dumps(req) + "\n").encode('utf-8'))
            
            data = b""
            while True:
                chunk = sock.recv(65536)
                if not chunk: break
                data += chunk
            sock.close()
            
            remote_history = json.loads(data.decode('utf-8'))
            new_count = 0
            for msg_data in remote_history:
                msg_id = msg_data.get("id")
                if msg_id not in self.history:
                    msg_data['is_sync'] = True
                    self.history[msg_id] = msg_data
                    self._ui_render_msg(msg_data)
                    new_count += 1
                    
            self._ui_system_msg(f"✅ 同步完成！获取到 {new_count} 条新消息。")
        except Exception as e:
            self._ui_system_msg(f"❌ 同步失败: {str(e)}")

    def _notify_ui_peers(self):
        if self.window:
            with self.peer_lock:
                peer_list = [{"name": p["name"], "ip": p["ip"]} for p in self.online_peers.values()]
            json_str = json.dumps(peer_list)
            self.window.evaluate_js(f"updateOnlineList({json_str})")

    def _ui_system_msg(self, text):
        if self.window:
            self.window.evaluate_js(f"renderSystemMsg('{text}')")

    def _ui_render_msg(self, msg_data):
        if self.window:
            json_str = json.dumps(msg_data)
            self.window.evaluate_js(f"renderMessage({json_str})")

if __name__ == '__main__':
    api = ChatAPI()
    
    window = webview.create_window(
        title='TUTalk', 
        html=HTML_CONTENT, 
        js_api=api,
        width=900, 
        height=650,
        background_color='#ededed'
    )
    
    api.window = window
    webview.start()
