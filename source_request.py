import os
import sys
import time
import base64
import ctypes
import winreg
import requests
import netifaces
import subprocess
import image_base64
from PIL import ImageTk
import customtkinter as ctk
from threading import Thread
from PyQt5.QtCore import QPoint
from win32com.client import Dispatch
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QAction, QMenu



class MyApp:
    def __init__(self, root):
        
        self.root = root
        
        self.request_interval = 5     #The time between two requests
        self.max_times_request = 120  #Number of requests between two logins, each login is 10 minutes apart(600s)
        self.last_click_time = 0

        self.key_interval = "interval"

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
            anchor="nw",
            text="000.000.000.000",
        )
        self.ip_label.grid(row=0, column=0, padx=7,pady=5, sticky="w")
        

        self.interval_menu = ctk.CTkOptionMenu(
            self.control_frame,
            width = 146,
            values = ["1s", "2s", "3s", "5s","7s","10s","15s"],
            variable = ctk.StringVar(value = str(self.request_interval) + 's'),
            command = self.change_request_interval,
            font = ("JetBrains Mono", 14,"bold"),
            dropdown_text_color = "#ffffff",
            dropdown_fg_color = "#004275",
            dropdown_hover_color = "#002642",
        )
        self.interval_menu.grid(row=1, column=0, padx=7,pady=4, sticky="w")
        

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
        Thread(target=self.login).start()
        self.current_times_request = self.max_times_request
        self.current_times_error = 0
        self.wait = 1
        self.running = True
        

    def run_background(self):
        self.current_times_request = self.max_times_request
        self.current_times_error = 0
        self.time = None
        self.wait = 0.0

        while self.start_app:
            
            if self.wait > 0:
                self.wait -= 0.2
                time.sleep(0.2)
                continue
                
            if self.running:
                if self.current_times_request >= self.max_times_request:
                    if self.login():
                        self.time = time.strftime("%H:%M")
                        self.current_times_request = 0
                        self.current_times_error = 0
                        # print('request true')
                    else:
                        if self.current_times_error >= int(90/self.request_interval):
                            self.running = False
                            self.status_label.configure(text="Status: Pause", text_color = "yellow")
                            self.info_label.configure(text=f"Time: {time.strftime('%H:%M')}")
                            # print('running false')
                            continue

                        self.current_times_error += 1
                        self.status_label.configure(text="Status: Error", text_color = "red")
                        self.info_label.configure(text=f"Count: {self.current_times_error}/{int(90/self.request_interval)}")

                        # print('request false')
                        self.wait = self.request_interval
                        continue

                if not self.check_internet():
                    self.current_times_request = self.max_times_request
                    # print('check_internet false')
                    continue
                # else:
                # print('check_internet true')

                self.current_times_request += 1
                self.status_label.configure(text="Status: Running", text_color = "green")
                self.info_label.configure(text=f"Time: {self.time}\nCount: {self.current_times_request}/{self.max_times_request}")
            
            
            self.wait = self.request_interval


    def login(self):
        try:
            ip = self.get_router_ip()
            if ip == '':
                self.ip_label.configure(text = '0.0.0.0')
                return False
            
            self.ip_label.configure(text = ip)

            requests.get(f'http://{ip}/logout?', timeout = 2)
            requests.post(f'http://{ip}/login', data = {'username': 'awing15-15', 'password': 'Awing15-15@2023'}, timeout = 2)
            return True
        except requests.RequestException as e:
            return False

    def check_internet(self):
        try:
            result = subprocess.run(['ping', '-n', '1', '-l', '1', '203.162.4.191'],timeout = 3, 
                                    stdout = subprocess.PIPE,
                                    stderr = subprocess.PIPE, 
                                    creationflags = subprocess.CREATE_NO_WINDOW).stdout.decode('utf-8')
        except subprocess.TimeoutExpired:
            return False

        if 'time' in result:
            return True
        else:
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
        self.tray_icon.setToolTip("Request")

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
        

    def change_request_interval(self, value):
        value = int(value[:-1]) #omit the 's' symbol
        if self.request_interval == value:
            return
        self.request_interval = value
        self.max_times_request = int(600 / self.request_interval)
        self.current_times_request = self.max_times_request
        self.current_times_error = 0
        self.wait = 0
        self.save_winreg_variables(self.key_interval, value)


    def load_data(self):
        request_interval = self.get_winreg_variables(self.key_interval)
        if request_interval is None:
            return
        self.request_interval = request_interval
        self.max_times_request = int(600 / self.request_interval)


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
