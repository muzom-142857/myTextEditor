import curses
import ctypes
import os
import sys
import locale
import re

# C++ 공유 라이브러리 로드
lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), 'libTextEditor.so'))

# C++ 함수 타입 지정
lib.createBuffer.restype = ctypes.c_void_p
lib.destroyBuffer.argtypes = [ctypes.c_void_p]
lib.loadFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lib.saveFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lib.getLineCount.argtypes = [ctypes.c_void_p]
lib.getLineCount.restype = ctypes.c_size_t
lib.getLine.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_size_t)]
lib.getLine.restype = None
lib.freeString.argtypes = [ctypes.c_char_p]
lib.freeString.restype = None
lib.insertText.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_size_t]
lib.deleteText.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
lib.splitLine.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t]
lib.joinLines.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
lib.getUnicodeLength.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
lib.getUnicodeLength.restype = ctypes.c_size_t
lib.copyText.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
lib.pasteText.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t]
lib.replaceAll.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
lib.findNext.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
lib.findNext.restype = None
lib.findByteInLine = lib.find_byte_in_line
lib.findByteInLine.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint8]
lib.findByteInLine.restype = ctypes.c_ssize_t

class CHighlightedToken(ctypes.Structure):
    _fields_ = [("start", ctypes.c_size_t),
                ("end", ctypes.c_size_t),
                ("token_type", ctypes.c_uint8)]

lib.get_highlighted_tokens.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
lib.get_highlighted_tokens.restype = ctypes.POINTER(CHighlightedToken)
lib.free_tokens.argtypes = [ctypes.POINTER(CHighlightedToken), ctypes.c_size_t]
lib.undoBuffer.argtypes = [ctypes.c_void_p]
lib.redoBuffer.argtypes = [ctypes.c_void_p]

# Color pair definitions
COLOR_PAIR_DEFAULT = 1
COLOR_PAIR_KEYWORD = 2
COLOR_PAIR_STRING = 3
COLOR_PAIR_COMMENT = 4


# 모드 정의
INSERT_MODE = 0
COMMAND_MODE = 1

# 전역 변수
buffers = [] # List to hold buffer objects
current_buffer_index = 0
last_search_term = ""

class Buffer:
    def __init__(self, filename, buffer_ptr):
        self.filename = filename
        self.buffer_ptr = buffer_ptr
        self.cursorY = 0
        self.cursorX = 0
        self.viewportTop = 0
        self.viewportLeft = 0
        self.currentMode = INSERT_MODE
        self.command = ""

def getPythonLine(buffer_ptr, lineNumber):
    linePtr = ctypes.c_char_p()
    lineLength = ctypes.c_size_t()
    lib.getLine(buffer_ptr, lineNumber, ctypes.byref(linePtr), ctypes.byref(lineLength))
    if linePtr.value:
        line = linePtr.value.decode('utf-8')
        lib.freeString(linePtr)
        return line
    return ""

def draw_explorer(win, path, selected_index):
    win.clear()
    win.border()
    win.addstr(0, 2, " File Explorer ")
    
    display_list = []
    if os.path.abspath(path) != '/':
        display_list.append("..")

    try:
        files = sorted(os.listdir(path))
        display_list.extend(files)
    except OSError as e:
        win.addstr(1, 2, f"Error: {e.strerror}")

    for i, file in enumerate(display_list):
        if i == selected_index:
            win.addstr(i + 1, 2, file, curses.A_REVERSE)
        else:
            win.addstr(i + 1, 2, file)
    win.refresh()

def draw_editor(win, buffer, mode, command):
    buffer_ptr = buffer.buffer_ptr
    viewportTop = buffer.viewportTop
    viewportLeft = buffer.viewportLeft
    cursorY = buffer.cursorY
    cursorX = buffer.cursorX
    
    height, width = win.getmaxyx()
    win.clear()
    lineCount = lib.getLineCount(buffer_ptr)
    lineNumberWidth = len(str(lineCount)) + 1

    token_type_map = {
        0: COLOR_PAIR_KEYWORD,
        1: COLOR_PAIR_STRING,
        2: COLOR_PAIR_COMMENT,
        3: COLOR_PAIR_DEFAULT
    }

    for i in range(height - 2): # Leave space for status bar
        lineNum = viewportTop + i
        if lineNum < lineCount:
            line = getPythonLine(buffer_ptr, lineNum)
            lineNumberText = str(lineNum + 1).rjust(lineNumberWidth)
            win.addstr(i, 0, lineNumberText, curses.A_DIM)

            token_count = ctypes.c_size_t()
            tokens_ptr = lib.get_highlighted_tokens(buffer_ptr, lineNum, ctypes.byref(token_count))
            tokens = tokens_ptr[:token_count.value]

            last_end = 0
            for token in tokens:
                if token.start > last_end:
                    win.addstr(i, lineNumberWidth + 1 + last_end - viewportLeft, line[last_end:token.start], curses.color_pair(COLOR_PAIR_DEFAULT))
                
                color = curses.color_pair(token_type_map.get(token.token_type, COLOR_PAIR_DEFAULT))
                win.addstr(i, lineNumberWidth + 1 + token.start - viewportLeft, line[token.start:token.end], color)
                last_end = token.end

            if last_end < len(line):
                win.addstr(i, lineNumberWidth + 1 + last_end - viewportLeft, line[last_end:], curses.color_pair(COLOR_PAIR_DEFAULT))

            lib.free_tokens(tokens_ptr, token_count.value)

    modeText = {INSERT_MODE: "INSERT", COMMAND_MODE: "COMMAND"}[mode]
    statusMsg = f"File: {buffer.filename} | Mode: {modeText} | Pos: {cursorY+1}, {cursorX+1}"
    win.addstr(height - 1, 0, statusMsg, curses.A_REVERSE)

    if mode == COMMAND_MODE:
        command_text = ":" + command
        win.addstr(height - 1, 0, command_text)
    
    win.move(cursorY - viewportTop, cursorX - viewportLeft + lineNumberWidth + 1)
    win.refresh()

def main(stdscr):
    global buffers, current_buffer_index, last_search_term
    locale.setlocale(locale.LC_ALL, '')
    curses.cbreak()
    stdscr.keypad(True)
    curses.use_default_colors()

    curses.start_color()
    curses.init_pair(COLOR_PAIR_DEFAULT, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(COLOR_PAIR_KEYWORD, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(COLOR_PAIR_STRING, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(COLOR_PAIR_COMMENT, curses.COLOR_GREEN, curses.COLOR_BLACK)

    height, width = stdscr.getmaxyx()
    explorer_width = 30
    editor_width = width - explorer_width

    tab_height = 1
    tab_win = curses.newwin(tab_height, width, 0, 0)
    editor_win = curses.newwin(height - tab_height, editor_width, tab_height, explorer_width)
    explorer_win = curses.newwin(height - tab_height, explorer_width, tab_height, 0)

    active_win = editor_win
    
    initial_filename = sys.argv[1] if len(sys.argv) > 1 else "untitled.txt"
    initial_buffer_ptr = lib.createBuffer()
    lib.loadFile(initial_buffer_ptr, initial_filename.encode('utf-8'))
    buffers.append(Buffer(initial_filename, initial_buffer_ptr))

    explorer_path = "."
    explorer_selected_index = 0

    while True:
        if not buffers:
            break

        current_buffer = buffers[current_buffer_index]

        tab_win.clear()
        x_offset = 0
        for i, buf in enumerate(buffers):
            tab_name = os.path.basename(buf.filename)
            style = curses.A_REVERSE if i == current_buffer_index else curses.A_NORMAL
            tab_win.addstr(0, x_offset, f" {tab_name} ", style)
            x_offset += len(tab_name) + 3
        tab_win.refresh()

        draw_explorer(explorer_win, explorer_path, explorer_selected_index)
        draw_editor(editor_win, current_buffer, current_buffer.currentMode, current_buffer.command)

        active_window = explorer_win if active_win == explorer_win else editor_win
        key = active_window.getch()

        if key == 23: # Ctrl+W
            active_win = editor_win if active_win == explorer_win else explorer_win
            continue
        elif key == curses.KEY_F2:
            current_buffer_index = (current_buffer_index + 1) % len(buffers)
            continue
        elif key == curses.KEY_F3:
            current_buffer_index = (current_buffer_index - 1 + len(buffers)) % len(buffers)
            continue
        elif key == 26: # Ctrl+Z
            lib.undoBuffer(current_buffer.buffer_ptr)
            continue
        elif key == 25: # Ctrl+Y
            lib.redoBuffer(current_buffer.buffer_ptr)
            continue

        if active_win == editor_win:
            if key == 27: # Esc
                if current_buffer.currentMode == INSERT_MODE:
                    current_buffer.currentMode = COMMAND_MODE
                    current_buffer.command = ""
                else:
                    current_buffer.currentMode = INSERT_MODE
            elif current_buffer.currentMode == INSERT_MODE:
                if key == curses.KEY_UP:
                    current_buffer.cursorY = max(0, current_buffer.cursorY - 1)
                elif key == curses.KEY_DOWN:
                    lineCount = lib.getLineCount(current_buffer.buffer_ptr)
                    current_buffer.cursorY = min(lineCount - 1, current_buffer.cursorY + 1)
                elif key == curses.KEY_LEFT:
                    current_buffer.cursorX = max(0, current_buffer.cursorX - 1)
                elif key == curses.KEY_RIGHT:
                    line = getPythonLine(current_buffer.buffer_ptr, current_buffer.cursorY)
                    current_buffer.cursorX = min(len(line), current_buffer.cursorX + 1)
                elif key == 10: # Enter
                    lib.splitLine(current_buffer.buffer_ptr, current_buffer.cursorY, current_buffer.cursorX)
                    current_buffer.cursorY += 1
                    current_buffer.cursorX = 0
                elif key == curses.KEY_BACKSPACE or key == 127:
                    if current_buffer.cursorX > 0:
                        lib.deleteText(current_buffer.buffer_ptr, current_buffer.cursorY, current_buffer.cursorX, 1)
                        current_buffer.cursorX -= 1
                    elif current_buffer.cursorY > 0:
                        lastLineLength = lib.getUnicodeLength(current_buffer.buffer_ptr, current_buffer.cursorY - 1)
                        lib.joinLines(current_buffer.buffer_ptr, current_buffer.cursorY)
                        current_buffer.cursorY -= 1
                        current_buffer.cursorX = lastLineLength
                else:
                    try:
                        input_char = chr(key)
                        input_bytes = input_char.encode('utf-8')
                        lib.insertText(current_buffer.buffer_ptr, current_buffer.cursorY, current_buffer.cursorX, input_bytes, len(input_bytes))
                        current_buffer.cursorX += 1
                    except (ValueError, curses.error):
                        pass # Ignore invalid characters
            elif current_buffer.currentMode == COMMAND_MODE:
                if key == 10: # Enter
                    parse_command(current_buffer, current_buffer.command)
                    current_buffer.currentMode = INSERT_MODE
                    current_buffer.command = ""
                elif key == curses.KEY_BACKSPACE or key == 127:
                    current_buffer.command = current_buffer.command[:-1]
                elif 32 <= key <= 126:
                    current_buffer.command += chr(key)

        elif active_win == explorer_win:
            display_list = [".."] if os.path.abspath(explorer_path) != '/' else []
            try:
                display_list.extend(sorted(os.listdir(explorer_path)))
            except OSError:
                pass

            if key == curses.KEY_UP:
                explorer_selected_index = max(0, explorer_selected_index - 1)
            elif key == curses.KEY_DOWN:
                explorer_selected_index = min(len(display_list) - 1, explorer_selected_index + 1)
            elif key == 10: # Enter
                selected_item = display_list[explorer_selected_index]
                selected_path = os.path.join(explorer_path, selected_item)
                
                if selected_item == "..":
                    explorer_path = os.path.dirname(explorer_path)
                    explorer_selected_index = 0
                elif os.path.isdir(selected_path):
                    explorer_path = selected_path
                    explorer_selected_index = 0
                elif os.path.isfile(selected_path):
                    already_open = False
                    for i, buf in enumerate(buffers):
                        if os.path.abspath(buf.filename) == os.path.abspath(selected_path):
                            current_buffer_index = i
                            already_open = True
                            break
                    if not already_open:
                        new_buffer_ptr = lib.createBuffer()
                        lib.loadFile(new_buffer_ptr, selected_path.encode('utf-8'))
                        buffers.append(Buffer(selected_path, new_buffer_ptr))
                        current_buffer_index = len(buffers) - 1
                    active_win = editor_win

        # Viewport logic
        height, width = editor_win.getmaxyx()
        lineCount = lib.getLineCount(current_buffer.buffer_ptr)
        lineNumberWidth = len(str(lineCount)) + 1
        
        if current_buffer.cursorY < current_buffer.viewportTop:
            current_buffer.viewportTop = current_buffer.cursorY
        if current_buffer.cursorY >= current_buffer.viewportTop + height - 1:
            current_buffer.viewportTop = current_buffer.cursorY - (height - 2)
        if current_buffer.cursorX < current_buffer.viewportLeft:
            current_buffer.viewportLeft = current_buffer.cursorX
        if current_buffer.cursorX >= current_buffer.viewportLeft + width - lineNumberWidth - 1:
            current_buffer.viewportLeft = current_buffer.cursorX - (width - lineNumberWidth - 2)

    for buf in buffers:
        lib.destroyBuffer(buf.buffer_ptr)

def parse_command(buffer, command):
    global buffers, current_buffer_index, last_search_term
    
    if not command:
        return

    parts = command.split(' ')
    cmd = parts[0]
    args = parts[1:]

    if cmd == 'q':
        if len(buffers) > 1:
            lib.destroyBuffer(buffer.buffer_ptr)
            buffers.pop(current_buffer_index)
            current_buffer_index = max(0, current_buffer_index - 1)
        else:
            # Quit if this is the last buffer
            lib.destroyBuffer(buffer.buffer_ptr)
            buffers.pop(current_buffer_index)
    elif cmd == 'qa':
        sys.exit(0)
    elif cmd == 'w':
        filename = args[0] if args else buffer.filename
        lib.saveFile(buffer.buffer_ptr, filename.encode('utf-8'))
        buffer.filename = filename
    elif cmd == 'wq':
        lib.saveFile(buffer.buffer_ptr, buffer.filename.encode('utf-8'))
        lib.destroyBuffer(buffer.buffer_ptr)
        buffers.pop(current_buffer_index)
        current_buffer_index = max(0, current_buffer_index - 1)
    elif cmd.startswith('%s/'):
        try:
            _, old, new, g = re.split(r'/(?!\)', command)
            if g == 'g':
                lib.replaceAll(buffer.buffer_ptr, old.encode('utf-8'), new.encode('utf-8'))
        except ValueError:
            pass # Ignore invalid replace commands
    elif cmd.startswith('/'):
        term = command[1:]
        last_search_term = term
        found_y, found_x = ctypes.c_size_t(), ctypes.c_size_t()
        lib.findNext(buffer.buffer_ptr, term.encode('utf-8'), buffer.cursorY, buffer.cursorX + 1, ctypes.byref(found_y), ctypes.byref(found_x))
        buffer.cursorY, buffer.cursorX = found_y.value, found_x.value
    elif cmd.isdigit():
        buffer.cursorY = min(int(cmd) - 1, lib.getLineCount(buffer.buffer_ptr) - 1)
        buffer.cursorX = 0
    elif cmd == '
:
        buffer.cursorY = lib.getLineCount(buffer.buffer_ptr) - 1
        buffer.cursorX = 0


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except curses.error as e:
        print(f"curses error: {e}")
        print("Terminal might be too small.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
