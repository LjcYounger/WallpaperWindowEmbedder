from key_movable_window import KeyMovableWindow
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import QUrl

class DynamicWindow(KeyMovableWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DynamicWindow")

        screen_size = self.screen().size()
        self.setGeometry(0, 0, screen_size.width(), screen_size.height())

        # 1. 创建视频显示部件
        self.video_widget = QVideoWidget()

        # 2. 创建媒体播放器和音频输出
        self.audio_output = QAudioOutput() # 负责声音
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget) # 将画面输出到 video_widget

        self.setCentralWidget(self.video_widget)


        # PySide6 接受 QUrl 格式的路径
        self.media_player.setSource(QUrl.fromLocalFile("test.mp4"))
        self.media_player.setLoops(-1)
        self.media_player.play()
        
