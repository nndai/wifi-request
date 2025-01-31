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
import customtkinter as ctk
from threading import Thread
from PIL import ImageTk
from PyQt5.QtCore import QPoint
from win32com.client import Dispatch
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QAction, QMenu

class MyApp:
    def __init__(self, root):

        self.ip = 'Auto'              #URL
        self.request_interval = 5     #The time between two requests
        self.max_times_request = 120  #Number of requests between two logins, each login is 10 minutes apart(600s)
        self.last_click_time = 0

        self.key_interval = "interval"
        self.key_ip = "ip"

        self.load_data()

        # ***GUI***
        self.root = root
        self.root.title("Request")
        self.root.geometry("370x150")
        
        ctk.set_default_color_theme("blue")
        self.root.resizable(False, False)

        self.remove_minimize_maximize()
        self.root._iconbitmap_method_called = True  # Prevents the icon from being overwritten by the default icon
        root.tk.call("wm", "iconphoto", root._w, ImageTk.PhotoImage(data=base64.b64decode(image_base64.APP_ICON_BASE64)))
        # self.root.attributes("-topmost", True)
        self.on_closing()

        self.text_label_frame = ctk.CTkFrame(root, border_color="blue",width=250,height=100)
        self.text_label_frame.place(x=15,y=14)

        self.text_label_info = ctk.CTkLabel(
            self.text_label_frame, 
            width=150, height=100, 
            font=("JetBrains Mono",14, "bold"), 
            justify="left", 
            anchor="nw", text="", 
            wraplength=380
        )
        self.text_label_info.pack(padx=10, pady=10)


        self.control_frame = ctk.CTkFrame(root,width=300,height=50)
        self.control_frame.place(x=200,y=14)

        self.menu_url = ctk.CTkOptionMenu(
            self.control_frame,
            values = ["25.25.0.1", "26.26.0.1", "27.27.0.1", "28.28.0.1", "Auto"],
            variable = ctk.StringVar(value=self.ip),
            command = self.change_ip,
            font = ("JetBrains Mono", 14, "bold"),
            dropdown_text_color = "#ffffff",
            dropdown_fg_color = "#004275",
            dropdown_hover_color = "#002642",
        )
        self.menu_url.grid(row=0, column=0, padx=7,pady=7)

        self.menu_interval = ctk.CTkOptionMenu(
            self.control_frame, 
            values = ["1s", "2s", "3s", "5s","7s","10s","15s"],
            variable = ctk.StringVar(value = str(self.request_interval) + 's'),
            command = self.change_request_interval,
            font = ("JetBrains Mono", 14,"bold"),
            dropdown_text_color = "#ffffff",
            dropdown_fg_color = "#004275",
            dropdown_hover_color = "#002642",
        )
        self.menu_interval.grid(row=1, column=0, padx=7,pady=4)

        self.button = ctk.CTkButton(
            self.control_frame, 
            text="Request", 
            command=self.login_by_button, 
            font=("JetBrains Mono", 14,"bold")
        )
        self.button.grid(row=2, column=0, padx=7,pady=7)
        # ********


        self.tray_thread = Thread(target=self.create_tray_icon)
        self.tray_thread.start()

        self.running = True
        self.thread = Thread(target=self.run_background)
        self.thread.start()


    def login_by_button(self):
        self.running = False
        current_time = time.time()
        if current_time - self.last_click_time < 1:
            self.running = True
            return
        
        self.last_click_time = current_time
        self.text_label_info.configure(text="Logging in......")
        Thread(target=self.login).start()
        self.current_times_request = self.max_times_request
        self.current_times_error = 0
        self.running = True

    def run_background(self):
        self.current_times_request = self.max_times_request
        self.current_times_error = 0
        self.time = None
        self.start_app = True

        while self.start_app:
            if self.running:
                if self.current_times_request >= self.max_times_request:
                    if self.login():
                        self.time = time.strftime("%H:%M")
                        self.current_times_request = 0
                        self.current_times_error = 0
                        #self.text_label_ip.configure(text=f"IP: {self.url}")
                        # print('request true')
                    else:
                        if self.current_times_error >= int(90/self.request_interval):
                            self.running = False
                            self.text_label_info.configure(text=f"Status: Pause\nTime: {time.strftime('%H:%M')}")
                            # print('running false')
                            continue

                        self.current_times_error += 1
                        self.text_label_info.configure(text=f"Status: Error\nCount: {self.current_times_error}/{int(90/self.request_interval)}")
                        # print('request false')
                        time.sleep(self.request_interval)
                        continue

                if not self.check_internet():
                    self.current_times_request = self.max_times_request
                    # print('check_internet false')
                    continue
                # else:
                # print('check_internet true')

                self.current_times_request += 1
                self.text_label_info.configure(text=f"Status: Running\nTime: {self.time}\nCount: {self.current_times_request}/{self.max_times_request}")
            time.sleep(self.request_interval)

    def login(self):
        try:
            ip = self.ip
            if ip == "Auto":
                ip = self.get_router_ip()
                if ip == '':
                    return False
                self.menu_url.set("Auto: " + ip.split('.')[0])

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
        self.start_app = False
        self.Qapp.quit()
        self.thread.join()
        self.root.quit()

    
    def change_ip(self, value):
        if self.ip == value and value != "Auto":
            return
        self.ip = value
        self.current_times_request = self.max_times_request
        self.current_times_error = 0
        self.save_winreg_variables(self.key_ip, value)

    def change_request_interval(self, value):
        value = int(value[:-1])
        if self.request_interval == value:
            return
        self.request_interval = value
        self.max_times_request = int(600 / self.request_interval)
        self.current_times_request = self.max_times_request
        self.current_times_error = 0
        self.save_winreg_variables(self.key_interval, value)


    def load_data(self):
        ip = self.get_winreg_variables(self.key_ip)
        if ip == "NoData":
            return
        self.ip = ip

        request_interval = self.get_winreg_variables(self.key_interval)
        if request_interval == "NoData":
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
            return "NoData"
    
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


if __name__ == "__main__":

    root = ctk.CTk()
    app = MyApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    add_to_startup_folder()
    root.mainloop()

    #Update: 01/01/2025
    #Version: v1.3
    #python -m PyInstaller --onefile --windowed --icon=app1.ico source_request.py
    #python -m PyInstaller source_request.spec
