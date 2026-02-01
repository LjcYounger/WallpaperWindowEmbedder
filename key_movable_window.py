import sys
import os
import json  # 替换为 json 模块
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import QThread, Signal, QPoint, QTimer
from pynput import keyboard

# 定义保存位置的文件名 (改为 .json 后缀，也可以是 .txt)
POS_FILE = "window_pos.json"

class KeyListenerThread(QThread):
    direction_signal = Signal(str)
    save_signal = Signal()

    def run(self):
        self.ctrl_pressed = False

        def on_press(key):
            try:

                if key == keyboard.Key.up:
                    self.direction_signal.emit('up')
                elif key == keyboard.Key.down:
                    self.direction_signal.emit('down')
                elif key == keyboard.Key.left:
                    self.direction_signal.emit('left')
                elif key == keyboard.Key.right:
                    self.direction_signal.emit('right')

                # 检测 Ctrl+S
                if hasattr(key, 'char') and key.char == '\x13':
                    self.save_signal.emit()

            except AttributeError:
                pass

        def on_release(key):
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

class KeyMovableWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        size = self.screen().size()
        self.setFixedSize(size.width(), size.height())

        QTimer.singleShot(100, self.apply_position)
        # 启动监听线程
        self.listener_thread = KeyListenerThread()
        self.listener_thread.direction_signal.connect(self.move_window)
        self.listener_thread.save_signal.connect(self.save_position)
        self.listener_thread.start()

    def move_window(self, direction):
        current_pos = self.pos()
        step = 1
        
        if direction == 'up':
            self.move(current_pos.x(), current_pos.y() - step)
        elif direction == 'down':
            self.move(current_pos.x(), current_pos.y() + step)
        elif direction == 'left':
            self.move(current_pos.x() - step, current_pos.y())
        elif direction == 'right':
            self.move(current_pos.x() + step, current_pos.y())

    def save_position(self):
        """使用 JSON 保存坐标"""
        pos = self.pos()
        try:
            with open(POS_FILE, 'w') as f:  # 注意是文本写入模式
                # 直接将包含两个数字的列表写入文件
                json.dump([pos.x()+8, pos.y()], f)
            print(f"位置已保存 (JSON): [{pos.x()}, {pos.y()}]")
        except Exception as e:
            print(f"保存失败: {e}")

    def load_position(self):
        """使用 JSON 读取坐标"""
        if os.path.exists(POS_FILE):
            try:
                with open(POS_FILE, 'r') as f:
                    # 读取列表 [x, y]
                    pos_data = json.load(f)
                    x, y = pos_data[0], pos_data[1]
                    return x, y
            except Exception as e:
                print(f"读取失败: {e}")
                return None
        return None

    def apply_position(self):
        """设置坐标"""
        # 启动时尝试加载位置
        pos = self.load_position()
        self.move(*pos if pos else (0, 0))
    def closeEvent(self, event):
        self.listener_thread.terminate()
        self.listener_thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = KeyMovableWindow()
    window.resize(300, 200)
    window.show()
    sys.exit(app.exec())