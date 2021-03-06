import types
from copy import deepcopy
from typing import Dict, Optional, List

from dataclasses import dataclass, field

from pybreak_gui.frame_state import FrameState

FrameUUID = str


@dataclass
class ChangeSet:
    var_name: str
    changed_in_frames: List[FrameState] = field(default_factory=list)


@dataclass
class FrameHistory:
    history: Dict[FrameUUID, FrameState] = field(default_factory=dict)
    location: Optional[FrameUUID] = None
    hist_index: int = 1  # indicates where we are in history

    def append(self, frame: types.FrameType):
        """
        Append the frame to the history, and update
        the current location. When we append a frame to the
        history, we implicitly update the current location
        to indicate where we're at in execution.
        """
        try:
            locals = deepcopy(frame.f_locals)
        except TypeError:
            locals = frame.f_locals
        frame_state = FrameState(
            frame,
            locals,
            entry_num=len(self.history)
        )
        self.location = frame_state.uuid  # always refers to latest EXECUTED frame. nothing to do with history...
        self.history[self.location] = frame_state
        self.hist_index = len(self.history) - 1  # move view back to latest frame

    @property
    def exec_frame(self) -> FrameState:
        """
        Retrieve the FrameState from the current
        location.
        """
        return self.history[self.location]

    @property
    def hist_frame(self) -> FrameState:
        return list(self.history.values())[self.hist_index]

    def rewind(self, n: int = 1) -> FrameState:
        self.hist_index = max(0, self.hist_index - n)
        return self.hist_frame

    def forward(self, n: int = 1) -> FrameState:
        self.hist_index = min(self.hist_index + n, len(self.history) - 1)
        return self.hist_frame

    @property
    def viewing_history(self):
        return self.hist_index != len(self.history) - 1

    def history_of_local(self, variable_name: str) -> ChangeSet:
        pass

    @property
    def hist_offset(self):
        stack_size = len(self.history)
        return stack_size - self.hist_index
