import curses

# Constants
KEY_ENTER = 10
KEY_ESC = 27
KEY_TAB = 9
KEY_BACKSPACE = 127

def _clamp(v, a, b): return max(a, min(b, v))

def _safe_add_string(win, y, x, s, attr=0):
    try:
        win.addstr(y, x, s, attr)
    except curses.error:
        pass

def _split_mnemonic(label: str):
    if '&' in label:
        i = label.index('&')
        if i + 1 < len(label):
            ch = label[i + 1]
            disp = label[:i] + label[i + 1:]
            return disp, ch.lower(), i
    return label, None, -1
