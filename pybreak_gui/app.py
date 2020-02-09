import asyncio
import inspect
import sys
import threading
import time
import types
from bdb import Bdb

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout import Layout, HSplit
from prompt_toolkit.lexers import DynamicLexer, PygmentsLexer
from prompt_toolkit.widgets import SearchToolbar, TextArea

from pybreak_gui.frame_history import FrameHistory


class Controller:
    paused: bool = True


class PybreakGui(Bdb):
    def __init__(self):
        super().__init__()
        self.paused = True
        self.buffer = Buffer()
        self.app_thread = threading.Thread(target=self.start_gui, args=(asyncio.get_event_loop(),))
        self.frame_history = FrameHistory()

        self.search_toolbar = SearchToolbar()

        def get_view_file():
            if len(self.frame_history.history) > 0:
                return self.frame_history.hist_frame.filename
            return ".py"

        self.text_area = TextArea(
            lexer=DynamicLexer(
                lambda: PygmentsLexer.from_filename(
                    get_view_file(), sync_from_start=False
                )
            ),
            search_field=self.search_toolbar,
            scrollbar=True,
            line_numbers=True,
        )
        self.container = HSplit(
            [
                self.text_area,
                self.search_toolbar,
            ]
        )

        kb = KeyBindings()

        @kb.add("c-q")
        def _(event: KeyPressEvent):
            self._quit()
            event.app.exit()

        @kb.add("c-n")
        def _(event):
            self.set_next(self.frame_history.exec_frame.raw_frame)
            self.paused = False  # allow another frame to be processed

        self.app = Application(
            full_screen=True,
            layout=Layout(container=self.container),
            key_bindings=kb,
        )
        self.app.loop = asyncio.get_event_loop()

    def start_gui(self, loop):
        asyncio.set_event_loop(loop)
        self.app.run()
        self.text_area.buffer.insert_text("HELLO WORLD")

    def start(self, frame):
        self.app_thread.start()
        super().set_trace(frame)

    def _quit(self):
        sys.settrace(None)
        self.quitting = True

    def user_call(self, frame: types.FrameType, argument_list):
        # if self.stop_here(frame):
        # self.frame_history.append(frame)
        pass

    def user_line(self, frame: types.FrameType):
        """
        This method is called from dispatch_line() when either
        stop_here() or break_here() yields True.
        i.e. when we stop OR break at this line.
         * stop_here() yields true if the frame lies below the frame where
         debugging started on the call stack. i.e. it will be called for
         every line after we start debugging.
         * break_here() yields true only if there's a breakpoint for this
         line
        """
        self.text_area.buffer.insert_text(f"FRAME = {frame.f_code.co_filename}:{frame.f_lineno}")
        if self.stop_here(frame):
            # print("frame", frame)
            self.text_area.buffer.insert_text(str(frame.f_code.co_filename) + str(frame.f_lineno) + "\n")
            self.frame_history.append(frame)
            # self.text_area.buffer.insert_text(f"STOPPING AT {frame.f_code.co_filename}:{frame.f_lineno}")

            while self.paused:
                time.sleep(.1)
            self.paused = True


def set_trace():
    pybreak = PybreakGui()
    frame = inspect.currentframe().f_back
    pybreak.start(frame)
