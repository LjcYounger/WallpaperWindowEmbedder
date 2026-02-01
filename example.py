from set_wallpaper_layer import set_wallpaper_layer
from pyside_video_window import DynamicWindow

from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = DynamicWindow()
window.show()
set_wallpaper_layer(window.windowTitle())
sys.exit(app.exec())