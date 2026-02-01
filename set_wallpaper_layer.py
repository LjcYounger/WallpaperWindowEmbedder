import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

# 窗口枚举回调函数（用于查找所有 WorkerW）
def _enum_windows_proc(hwnd, lParam):
    class_name = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, class_name, 256)
    if class_name.value == "WorkerW":
        # 将找到的 WorkerW 句柄添加到列表
        workerw_list.append(hwnd)
    return True

# 获取屏幕分辨率
def get_screen_size():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

# 主函数：将指定窗口嵌入桌面图标下层
def _embed_window_as_wallpaper(target_hwnd):
    # 1. Validate target window handle
    if not user32.IsWindow(target_hwnd):
        print("[ERROR]Target window handle is invalid or no longer exists.")
        return False

    # 2. Get Progman window handle
    progman = user32.FindWindowW("Progman", "Program Manager")
    if not progman:
        print("[ERROR]Failed to find Progman window.")
        return False
    print(f"[DEBUG]Found Progman: 0x{progman:X}")

    # 3. Send 0x052C message to trigger WorkerW creation
    user32.SendMessageW(progman, 0x052C, 0, 0)
    print("[DEBUG]Sent 0x052C message to trigger desktop structure update")

    # Wait briefly for system to create windows
    time.sleep(0.1)

    # 4. Enumerate all WorkerW windows
    global workerw_list
    workerw_list = []
    ENUMWNDPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(ENUMWNDPROC(_enum_windows_proc), 0)

    if len(workerw_list) < 2:
        print("[ERROR]Insufficient WorkerW windows found; expected at least 2.")
        return False
    print(f"[DEBUG]Found {len(workerw_list)} WorkerW window(s)")

    # 5. Locate the WorkerW that contains SHELLDLL_DefView (desktop icons container)
    shell_defview_container = None
    for workerw in workerw_list:
        if not user32.IsWindow(workerw):
            continue  # Skip invalid handles
        defview = user32.FindWindowExW(workerw, None, "SHELLDLL_DefView", None)
        if defview:
            shell_defview_container = workerw
            print(f"[DEBUG]Found icon container WorkerW: 0x{workerw:X}")
            break

    if not shell_defview_container:
        print("[ERROR]Could not locate WorkerW containing SHELLDLL_DefView.")
        return False

    # 6. Find the next WorkerW after the icon container (this one overlays the wallpaper)
    try:
        idx = workerw_list.index(shell_defview_container)
        if idx + 1 >= len(workerw_list):
            print("[DEBUG]Subsequent WorkerW has been removed.")
        else:
            candidate_workerw = workerw_list[idx + 1]

            if not user32.IsWindow(candidate_workerw):
                print("[WARNING]Candidate overlay WorkerW is no longer valid.")
                # Proceed anyway; it might have been destroyed by system
            else:
                print(f"[DEBUG]Candidate overlay WorkerW: 0x{candidate_workerw:X}")

                # Optional verification: next window after candidate should be Progman
                next_after_candidate = user32.GetWindow(candidate_workerw, 2)  # GW_HWNDNEXT
                if next_after_candidate != progman:
                    print("[WARNING]Candidate WorkerW is not followed by Progman; topology may have changed.")
                else:
                    print("[DEBUG]Topology verified: candidate WorkerW is correctly positioned.")

                # Close the overlay WorkerW
                print(f"[DEBUG]Closing overlay WorkerW: 0x{candidate_workerw:X}")
                user32.SendMessageW(candidate_workerw, 0x0010, 0, 0)  # WM_CLOSE

    except (ValueError, IndexError):
        print("[ERROR]Unexpected error locating candidate WorkerW.")
        return False

    # 7. Reparent target window under Progman
    if user32.SetParent(target_hwnd, progman):
        print(f"[DEBUG]Successfully reparented window 0x{target_hwnd:X} under Progman")

        # Adjust position and size (optional)
        #screen_size = get_screen_size()
        
        #user32.SetWindowPos(
        #    target_hwnd,
        #    -1,          # HWND_BOTTOM
        #    0, 0,        # x, y
        #    *screen_size,  # width, height (adjust per monitor if needed)
        #    0x0040 | 0x0001  # SWP_NOZORDER | SWP_NOREDRAW
        #)
        return True
    else:
        print("[ERROR]SetParent failed; could not embed window under desktop.")
        return False

# ================== 使用示例 ==================

# 示例：查找一个已知窗口并嵌入
def set_wallpaper_layer(window_title):
    target = user32.FindWindowW(None, window_title)
    if not target:
        print(f"[ERROR]Window with title '{window_title}' not found")
    else:
        print(f"[DEBUG]Found target window: 0x{target:X}")
        success = _embed_window_as_wallpaper(target)
        if success:
            print("[DEBUG]Embedding succeeded! Window is now displayed as desktop wallpaper below icons.")
        else:
            print("[ERROR]Embedding failed.")

def cancel_wallpaper_layer(window_title):
    progman = user32.FindWindowW("Progman", "Program Manager")
    target = user32.FindWindowExW(progman, None, 'SDL_app', window_title)
    if not target:
        print(f"[ERROR]Window with title '{window_title}' not found under Progman")
    else:
        print(f"[DEBUG]Found target window: 0x{target:X}")
        if user32.SetParent(target, None):
            print("[DEBUG]Successfully canceled background layer (window detached from Progman).")
        else:
            print("[ERROR]Failed to cancel background layer (SetParent failed).")

if __name__ == '__main__':
    cancel_background_layer('The Powder Toy')
