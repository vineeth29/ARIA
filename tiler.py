"""
ARIA Smart Window Tiler
========================
Arrange windows by voice command using win32gui.
"""

import ctypes, re

user32 = ctypes.windll.user32
SW_RESTORE = 9
SW_MAXIMIZE = 3
SW_MINIMIZE = 6

def _get_all_windows():
    windows = []
    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if title and title not in ("Program Manager", "Settings"):
                    windows.append({"hwnd": hwnd, "title": title})
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return windows

def find_window(name):
    name_lower = name.lower()
    for w in _get_all_windows():
        if name_lower in w["title"].lower():
            return w
    return None

def list_windows():
    windows = _get_all_windows()
    if not windows:
        return "  No visible windows found."
    lines = ["  Open Windows:"]
    for i, w in enumerate(windows[:20], 1):
        lines.append(f"    {i}. {w['title'][:60]}")
    return "\n".join(lines)

def _get_work_area():
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                     ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    rect = RECT()
    ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right, rect.bottom

def _move_window(hwnd, x, y, w, h):
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetWindowPos(hwnd, 0, x, y, w, h, 0x0004)
    user32.SetForegroundWindow(hwnd)

def snap_left(name):
    w = find_window(name)
    if not w: return f"  Window '{name}' not found."
    l, t, r, b = _get_work_area()
    _move_window(w["hwnd"], l, t, (r-l)//2, b-t)
    return f"  ✅ '{w['title'][:40]}' snapped left."

def snap_right(name):
    w = find_window(name)
    if not w: return f"  Window '{name}' not found."
    l, t, r, b = _get_work_area()
    hw = (r-l)//2
    _move_window(w["hwnd"], l+hw, t, hw, b-t)
    return f"  ✅ '{w['title'][:40]}' snapped right."

def snap_top_left(name):
    w = find_window(name)
    if not w: return f"  Window '{name}' not found."
    l, t, r, b = _get_work_area()
    _move_window(w["hwnd"], l, t, (r-l)//2, (b-t)//2)
    return f"  ✅ '{w['title'][:40]}' snapped top-left."

def snap_top_right(name):
    w = find_window(name)
    if not w: return f"  Window '{name}' not found."
    l, t, r, b = _get_work_area()
    hw = (r-l)//2
    _move_window(w["hwnd"], l+hw, t, hw, (b-t)//2)
    return f"  ✅ '{w['title'][:40]}' snapped top-right."

def snap_bottom_left(name):
    w = find_window(name)
    if not w: return f"  Window '{name}' not found."
    l, t, r, b = _get_work_area()
    hh = (b-t)//2
    _move_window(w["hwnd"], l, t+hh, (r-l)//2, hh)
    return f"  ✅ '{w['title'][:40]}' snapped bottom-left."

def snap_bottom_right(name):
    w = find_window(name)
    if not w: return f"  Window '{name}' not found."
    l, t, r, b = _get_work_area()
    hw, hh = (r-l)//2, (b-t)//2
    _move_window(w["hwnd"], l+hw, t+hh, hw, hh)
    return f"  ✅ '{w['title'][:40]}' snapped bottom-right."

def maximize(name):
    w = find_window(name)
    if not w: return f"  Window '{name}' not found."
    user32.ShowWindow(w["hwnd"], SW_MAXIMIZE)
    return f"  ✅ '{w['title'][:40]}' maximized."

def minimize(name):
    w = find_window(name)
    if not w: return f"  Window '{name}' not found."
    user32.ShowWindow(w["hwnd"], SW_MINIMIZE)
    return f"  ✅ '{w['title'][:40]}' minimized."

def tile_all():
    windows = _get_all_windows()
    if not windows: return "  No windows to tile."
    l, t, r, b = _get_work_area()
    sw, sh = r-l, b-t
    n = len(windows)
    if n == 1:
        _move_window(windows[0]["hwnd"], l, t, sw, sh)
    elif n == 2:
        hw = sw//2
        _move_window(windows[0]["hwnd"], l, t, hw, sh)
        _move_window(windows[1]["hwnd"], l+hw, t, hw, sh)
    elif n <= 4:
        hw, hh = sw//2, sh//2
        pos = [(l,t),(l+hw,t),(l,t+hh),(l+hw,t+hh)]
        for i, w in enumerate(windows[:4]):
            _move_window(w["hwnd"], pos[i][0], pos[i][1], hw, hh)
    else:
        cols, rows = 3, (min(n,9)+2)//3
        cw, ch = sw//cols, sh//rows
        for i, w in enumerate(windows[:9]):
            _move_window(w["hwnd"], l+(i%cols)*cw, t+(i//cols)*ch, cw, ch)
    return f"  ✅ Tiled {min(n,9)} windows."

def parse_tile_command(text):
    text_lower = text.lower()
    if "tile all" in text_lower: return tile_all()
    if "list window" in text_lower or "show window" in text_lower: return list_windows()
    m = re.search(r'put\s+(.+?)\s+on\s+left.*?(\w[\w\s]+?)\s+on\s+right', text_lower)
    if m: return snap_left(m.group(1).strip()) + "\n" + snap_right(m.group(2).strip())
    m = re.search(r'maximize\s+(.+)', text_lower)
    if m: return maximize(m.group(1).strip())
    m = re.search(r'minimize\s+(.+)', text_lower)
    if m: return minimize(m.group(1).strip())
    m = re.search(r'snap\s+(.+?)\s+to\s+(left|right|top.?left|top.?right|bottom.?left|bottom.?right)', text_lower)
    if m:
        pos = m.group(2).replace("-","").replace(" ","")
        funcs = {"left":snap_left,"right":snap_right,"topleft":snap_top_left,"topright":snap_top_right,"bottomleft":snap_bottom_left,"bottomright":snap_bottom_right}
        f = funcs.get(pos)
        if f: return f(m.group(1).strip())
    return None
