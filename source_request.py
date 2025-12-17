import os
import re
import sys
import time
import base64
import ctypes
import winreg
import requests
import datetime
import netifaces
import subprocess
import image_base64
import urllib.parse
from PIL import ImageTk
import customtkinter as ctk
from threading import Thread
from bs4 import BeautifulSoup
from PyQt5.QtCore import QPoint
from win32com.client import Dispatch
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QAction, QMenu



class MyApp:
    def __init__(self, root):
        
        self.version = '1.5'
        
        self.root = root
        
        self.internet_check_interval = 5        #(second), the time between two internet checks or login attempts
        self.login_interval = 600               #(second), time between two logins
        self.login_retry_duration = 5 * 60      #(second), max time to retry login if failed
        self.last_click_time = 0
        self.never_time = 60 * 60 * 24 * 7      #~1week, never pause relogin

        self.key_internet_check_interval = "internet_check_interval"
        self.key_login_retry_duration = "login_retry_duration"

        self.load_data()
        self.init_window()
        

        self.tray_thread = Thread(target=self.create_tray_icon)
        self.tray_thread.start()

        self.start_app = True
        self.running = True
        self.run_thread = Thread(target=self.run_background)
        self.run_thread.start()



    def init_window(self):
        self.root.title("Request")
        self.root.geometry("375x150")
        
        ctk.set_default_color_theme("blue")
        self.root.resizable(False, False)

        self.remove_minimize_maximize()
        self.root._iconbitmap_method_called = True  # Prevents the icon from being overwritten by the default icon
        root.tk.call("wm", "iconphoto", root._w, ImageTk.PhotoImage(data=base64.b64decode(image_base64.APP_ICON_BASE64)))
        # self.root.attributes("-topmost", True)
        self.on_closing()

        self.info_frame = ctk.CTkFrame(root, border_color="blue",width=250,height=100)
        self.info_frame.place(x=15,y=15)
        
        self.status_label = ctk.CTkLabel(
            self.info_frame, 
            width=150, height=10, 
            font=("JetBrains Mono",14 ,"bold"), 
            justify="left", 
            anchor="nw", text="", 
            wraplength=380
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")

        self.info_label = ctk.CTkLabel(
            self.info_frame, 
            width=150, height=89, 
            font=("JetBrains Mono",14 ,"bold"), 
            justify="left", 
            anchor="nw", text="", 
            wraplength=380
        )
        self.info_label.grid(row=1, column=0, padx=10, pady=0, sticky="w")
        

        
        self.control_frame = ctk.CTkFrame(root,width=300,height=50)
        self.control_frame.place(x=200,y=15)
        
        self.ip_frame = ctk.CTkFrame(self.control_frame, width=300,height=10, fg_color = "#1f6aa5",)
        self.ip_frame.grid(row=0, column=0, padx=7,pady=7, sticky="w")
        self.ip_label = ctk.CTkLabel(
            self.ip_frame,
            width=131, height=13, 
            font=("JetBrains Mono", 14, "bold"), 
            anchor="center",
            text="0.0.0.0",
        )
        self.ip_label.grid(row=0, column=0, padx=7,pady=5, sticky="w")
        

        self.interval_menu = ctk.CTkOptionMenu(
            self.control_frame,
            width = 71,
            values = ["1s", "2s", "3s", "5s","7s","10s","15s"],
            variable = ctk.StringVar(value = str(self.internet_check_interval) + 's'),
            anchor = "center",
            command = self.change_internet_check_interval,
            font = ("JetBrains Mono", 14,"bold"),
            dropdown_text_color = "#ffffff",
            dropdown_fg_color = "#004275",
            dropdown_hover_color = "#002642",
            text_info= "Interval time",
            dropdown_font= ("JetBrains Mono", 11,"bold"),
            fg_text_info_color = "#203a4f",
        )
        self.interval_menu.grid(row=1, column=0, padx=7,pady=4, sticky="w")
        
        self.interval_relogin_menu = ctk.CTkOptionMenu(
            self.control_frame,
            width = 71,
            values = ["1m", "5m", "nv"],
            variable = ctk.StringVar(value = 'nv' if self.login_retry_duration == self.never_time 
                                     else str(int(self.login_retry_duration / 60)) + 'm'),
            anchor = "center",
            command = self.change_login_retry_duration,
            font = ("JetBrains Mono", 14,"bold"),
            dropdown_text_color = "#ffffff",
            dropdown_fg_color = "#004275",
            dropdown_hover_color = "#002642",
            text_info= "Relogin time",
            dropdown_font= ("JetBrains Mono", 11,"bold"),
            fg_text_info_color = "#203a4f",
            
        )
        self.interval_relogin_menu.grid(row=1, column=0, padx=(0, 7), sticky="e")
        

        self.button = ctk.CTkButton(
            self.control_frame,
            width = 146,
            text="Request", 
            command=self.login_by_button, 
            font=("JetBrains Mono", 14,"bold")
        )
        self.button.grid(row=2, column=0, padx=7,pady=7, sticky="w")
        
        
        
    def login_by_button(self):
        current_time = time.time()
        if current_time - self.last_click_time < 1:
            self.running = True
            return
        
        self.last_click_time = current_time
        self.status_label.configure(text="Logging in......", text_color = "white")
        self.info_label.configure(text="")
        #Thread(target=self.login).start()
        self.current_times_error = 0
        self.time_login = None
        self.wait = 1.0
        self.running = True
        

    def run_background(self):
        self.current_times_error = 0
        self.time_login = None
        self.wait = 0.0
        self.is_internet_connected = False

        
        def display_login_info():
            if self.time_login == None:
                return
            self.status_label.configure(text="Status: Running", text_color = "green")
            elapsed = int((datetime.datetime.now() - self.time_login).total_seconds())
            self.info_label.configure(text = f"TimeLogin: {self.time_login.strftime('%H:%M')}\n"f"TimeUsage: {elapsed//60:02d}:{elapsed%60:02d}")

        while self.start_app:
            
            if self.wait > 0:
                if self.is_internet_connected:
                    display_login_info()
                self.wait -= 0.5
                time.sleep(0.5)
                continue
                
            if self.running:
                is_login_success = False
                if self.time_login == None or (datetime.datetime.now() - self.time_login).total_seconds() >= self.login_interval:
                    self.is_internet_connected = False
                    
                    if self.login():
                        # successful login
                        is_login_success = True
                        self.time_login = datetime.datetime.now()
                        self.current_times_error = 0

                    else:
                        # pause
                        if self.current_times_error >= int(self.login_retry_duration/self.internet_check_interval):
                            self.running = False
                            self.status_label.configure(text="Status: Pause", text_color = "yellow")
                            self.info_label.configure(text=f"TimePause: {time.strftime('%H:%M')}")
                            print("\n-----App paused.-----\n")
                            continue

                        # handle error
                        self.current_times_error += 1
                        self.status_label.configure(text="Status: Error", text_color = "red")
                        if self.login_retry_duration == self.never_time:
                            self.info_label.configure(text=f"Attempt: {self.current_times_error}")
                        else:
                            self.info_label.configure(text=f"Attempt: {self.current_times_error}/{int(self.login_retry_duration/self.internet_check_interval)}")

                        self.wait = self.internet_check_interval
                        continue

                # check internet
                if not self.check_internet():
                    if is_login_success:
                        self.status_label.configure(text="Status: Error", text_color = "red")
                        self.info_label.configure(text="Login success but\nno internet!\nChecking...")
                        time.sleep(3)
                        
                        # check internet again
                        attempt = 0
                        max_attempts = 15
                        while not self.check_internet() and attempt < max_attempts:
                            self.info_label.configure(text="Login success but\nno internet!\nChecking...\nAttempt: " + str(attempt + 1) + "/" + str(max_attempts))
                            time.sleep(0.2)
                            attempt += 1
                            
                        if self.check_internet():
                            self.is_internet_connected = True
                            self.wait = self.internet_check_interval
                            continue
                            
                        self.status_label.configure(text="Status: Error", text_color = "red")
                        self.info_label.configure(text="Login success but\nno internet!\nRe-login")
                        
                    self.time_login = None
                    continue
                
                self.is_internet_connected = True
            
            self.wait = self.internet_check_interval


    def login(self):
        try:
            ip = self.get_router_ip()
            if ip == '':
                self.ip_label.configure(text = '0.0.0.0')
                print("---> Get Router IP failed.")
                return False
            
            self.ip_label.configure(text = ip)
            
            req = requests.get(f'http://{ip}/logout?', timeout = 2, allow_redirects=False)
            print("Logout: " + str(req.status_code))
            
        except requests.RequestException as e:
            print(f"Logout Request Exception: {e}")
            return False
        except Exception as e:
            print(f"Logout Exception: {e}")
            return False
        
        #time.sleep(0.5)
        
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        gateway_url = "http://192.168.200.1/login" # this ip address doesn't seem to be fixed
    
        try:
            resp_dummy = session.get(gateway_url, headers=headers, timeout = 2)
            
            redirect_url = self.process_interstitial_html(resp_dummy.text)
            if not redirect_url:
                print('\n' + resp_dummy.text)
                print("---> Không tìm thấy URL Redirect.")
                return False

            print(redirect_url)

        except Exception as e:
            print(f"[-] Lỗi kết nối Router: {e}")
            return False
        
        verify_url = "http://v1.awingconnect.vn/Home/VerifyUrl"
        
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': redirect_url,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
        })

        try:
            resp_verify = session.post(verify_url, timeout = 2)
            
            data = None
            try:
                data = resp_verify.json()
            except Exception as e:
                print('\n' + resp_verify.text)
                print(f"JSON Decode Exception: {e}")
                return False

            html_form = data['captiveContext']['contentAuthenForm']
            real_action_url = re.search(r'action="([^"]+)"', html_form).group(1)
            real_user = re.search(r'name="username" value="([^"]+)"', html_form).group(1)
            real_pass = re.search(r'name="password" value="([^"]+)"', html_form).group(1)
            
            print(f"User: {real_user}")
            print(f"Pass: {real_pass}")
            print(f"Action: {real_action_url}")

            final_payload = {
                'username': real_user,
                'password': real_pass,
                'dst': 'http://v1.awingconnect.vn/Success',
                'popup': 'false'
            }

            session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
            final_resp = session.post(real_action_url, data=final_payload, timeout = 2)

            if final_resp.status_code == 200 or final_resp.status_code == 302:
                print("[SUCCESS] Đã đăng nhập thành công!: " + str(final_resp.status_code) + "\n")
                return True
            
            print('\n' + final_resp.text)
            print(f"[FAIL] Server phản hồi: {final_resp.status_code}\n")
            return False

        except Exception as e:
            print(f"Login Exception: {e}\n")
            return False
        
    def process_interstitial_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        form = soup.find('form', id='authForm')
        
        if not form:
            print("Lỗi: Không tìm thấy form authForm trong HTML")
            return None
        
        base_url = form.get('action')
        
        params = {}
        for input_tag in form.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            
            if name:
                params[name] = value

        current_timestamp = int(time.time() * 1000)
        params['_t'] = str(current_timestamp)
        
        query_string = urllib.parse.urlencode(params)
        final_url = f"{base_url}?{query_string}"
        
        return final_url

    def check_internet(self):
        try:
            result = subprocess.run(['ping', '-n', '1', '-l', '1', '203.162.4.191'],timeout = 1, 
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE, 
                                    creationflags = subprocess.CREATE_NO_WINDOW).stdout.decode('utf-8')
        except subprocess.TimeoutExpired:
            print("Ping Timeout")
            return False
        
        if 'time' in result:
            return True
        return False

    def get_router_ip(self):
        router_ip = ''
        gateways = netifaces.gateways()
        default_gateway = gateways.get('default')
        if default_gateway and netifaces.AF_INET in default_gateway:
            router_ip = default_gateway[netifaces.AF_INET][0]
        return router_ip

    def create_tray_icon(self):
        self.Qapp = QApplication(sys.argv)
        self.tray_icon = QSystemTrayIcon(QIcon(self.get_qicon_from_base64(image_base64.APP_ICON_BASE64)))
        self.tray_icon.setToolTip("Request " + self.version)

        self.menu = QMenu()
        self.show_action = QAction(QIcon(self.get_qicon_from_base64(image_base64.SHOW_IMAGE_BASE64)), 'Show')
        self.show_action.triggered.connect(self.show_window)
        self.menu.addAction(self.show_action)

        self.exit_action = QAction(QIcon(self.get_qicon_from_base64(image_base64.EXIT_IMAGE_BASE64)), 'Exit')
        self.exit_action.triggered.connect(self.end_app)
        self.menu.addAction(self.exit_action)

        self.menu.setStyleSheet("""
            QMenu {
                background-color: #333333; /* Dark background */
                color: #FFFFFF; /* White text */
                border: 2px solid #666666; /* Border */
                border-radius: 5px; /* Rounded corners */
                padding: 5px 20px 5px 10px; /* Padding for the entire menu */
                font-family: Arial; /* Font family */
                font-weight: bold; /* Font weight */
            }
            QMenu::item {
                padding: 5px 20px 5px 10px;            
                border-radius: 5px; /* Rounded corners for menu items */
            }
            QMenu::item:selected {
                background-color: #666666; /* Hover background */
                border-radius: 5px; /* Rounded corners */                       
            }
        """)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()
        sys.exit(self.Qapp.exec_())
        

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.root.winfo_viewable():
                self.on_closing()
            else:
                self.show_window()
        if reason == QSystemTrayIcon.Context:
            cursor_pos = QCursor.pos()
            adjusted_pos = QPoint(cursor_pos.x() - 100 , cursor_pos.y() - 100)
            self.menu.popup(adjusted_pos)      

    def remove_minimize_maximize(self):
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
        style = style & ~0x00020000  # WS_MINIMIZEBOX
        style = style & ~0x00010000  # WS_MAXIMIZEBOX
        ctypes.windll.user32.SetWindowLongW(hwnd, -16, style)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0020 | 0x0004)

    def show_window(self):
        self.root.deiconify()
    def on_closing(self):
        self.root.withdraw()
    def end_app(self):
        self.on_closing()
        self.Qapp.quit()
        self.start_app = False
        self.run_thread.join()
        self.root.quit()
        sys.exit(0)
        

    def change_internet_check_interval(self, value):
        value = int(value[:-1]) #omit the 's' symbol
        if self.internet_check_interval == value:
            return
        
        self.internet_check_interval = value
        self.time_login = None
        self.current_times_error = 0
        self.wait = 0
        self.save_winreg_variables(self.key_internet_check_interval, value)
        
    def change_login_retry_duration(self, value):
        if value == 'nv':
            value = self.never_time
        else:
            value = 60 * int(value[:-1]) #omit the 'm' symbol
        if self.login_retry_duration == value:
            return
        self.login_retry_duration = value
        self.time_login = None
        self.current_times_error = 0
        self.wait = 0
        self.save_winreg_variables(self.key_login_retry_duration, value)

    def load_data(self):
        internet_check_interval = self.get_winreg_variables(self.key_internet_check_interval)
        if internet_check_interval != None:
            self.internet_check_interval = int(internet_check_interval)
            
        login_retry_duration = self.get_winreg_variables(self.key_login_retry_duration)
        if login_retry_duration != None:
            self.login_retry_duration = int(login_retry_duration)
            
    def save_winreg_variables(self, name, value):
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Software\\Request")
        if type(value) is str:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        else:
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
        winreg.CloseKey(key)

    def get_winreg_variables(self, name):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Request")
            value = winreg.QueryValueEx(key, name)[0]
            winreg.CloseKey(key)
            return value
        except FileNotFoundError:
            return None
    
    
    def get_qicon_from_base64(self, data_base64):
        image_data = base64.b64decode(data_base64)
        pixmap = QPixmap()
        if pixmap.loadFromData(image_data):
            return QIcon(pixmap)
        else:
            return None 
        

def add_to_startup_folder(app_name="request"):
    try:
        file_path = os.path.abspath(sys.argv[0])
        file_path = file_path[0].upper() + file_path[1:]
        startup_folder = os.path.join(
            os.getenv('APPDATA'),
            r"Microsoft\Windows\Start Menu\Programs\Startup"
        )

        shortcut_path = os.path.join(startup_folder, f"{app_name}.lnk")
        shell = Dispatch('WScript.Shell')

        if os.path.exists(shortcut_path):
            shortcut = shell.CreateShortcut(shortcut_path)
            if shortcut.TargetPath != file_path:
                print(shortcut.TargetPath)
                print(file_path)
                shortcut.TargetPath = file_path
                shortcut.WorkingDirectory = os.path.dirname(file_path)
                shortcut.Save()

        else:
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = file_path
            shortcut.WorkingDirectory = os.path.dirname(file_path)
            shortcut.Save()

    except Exception as e:
        pass

def check_single_instance():
    ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\RequestAppMutex")
    if ctypes.GetLastError() == 183:
        sys.exit(0)


if __name__ == "__main__":
    check_single_instance()
    
    root = ctk.CTk()
    app = MyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    add_to_startup_folder()
    root.mainloop()


    #python -m PyInstaller source_request.spec

###custom for dropdown_menu.py:105###
# if self._text_info != None:
#     self.add_command(
#         label=self._text_info.ljust(self._min_character_width),
#         command=None,
#         foreground=self._apply_appearance_mode(self._text_color),
#         background=self._apply_appearance_mode(self._fg_text_info_color),
#         activebackground=self._apply_appearance_mode(self._fg_text_info_color),
#         activeforeground=self._apply_appearance_mode(self._text_color)
#     )