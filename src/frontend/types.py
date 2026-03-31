"""DearPyGui variable wrappers and slot state for the lineup editor UI.

These classes bridge Tkinter-style variable APIs (StringVar / BooleanVar)
to DearPyGui widget values, so the rest of the codebase can use a familiar
``.get()`` / ``.set()`` interface.
"""

import dearpygui.dearpygui as dpg


class DPGVar:
    """tkinter.StringVar replacement backed by a DPG input item."""

    def __init__(self, tag=None, default=""):
        self._tag = tag
        self._value = str(default)

    def get(self) -> str:
        if self._tag and dpg.does_item_exist(self._tag):
            itype = dpg.get_item_info(self._tag).get("type", "")
            if "Button" in itype:
                label = dpg.get_item_configuration(self._tag).get("label")
                return str(label)
            val = dpg.get_value(self._tag)
            return str(val) if val is not None else self._value
        return self._value

    def set(self, value):
        self._value = str(value)
        if self._tag and dpg.does_item_exist(self._tag):
            itype = dpg.get_item_info(self._tag).get("type", "")
            if "Button" in itype:
                dpg.configure_item(self._tag, label=self._value)
            else:
                dpg.set_value(self._tag, self._value)


class DPGBoolVar:
    """tkinter.BooleanVar replacement backed by a DPG checkbox item."""

    def __init__(self, tag=None, default=False):
        self._tag = tag
        self._value = bool(default)

    def get(self) -> bool:
        if self._tag and dpg.does_item_exist(self._tag):
            return bool(dpg.get_value(self._tag))
        return self._value

    def set(self, value):
        self._value = bool(value)
        if self._tag and dpg.does_item_exist(self._tag):
            dpg.set_value(self._tag, self._value)

    def trace_add(self, mode, callback):
        pass

    def trace_remove(self, mode, name):
        pass


class SlotState:
    """Pure-data holder for a single performer slot; UI built by build_slot_row()."""

    _counter = 0

    def __init__(self, name="", genre="", duration=60):
        SlotState._counter += 1
        self._id = SlotState._counter
        self.name_var     = DPGVar(default=name)
        self.genre_var    = DPGVar(default=genre)
        self.duration_var = DPGVar(default=str(duration))
        self.row_tag      = None  # set by build_slot_row

    def destroy(self):
        """Remove the DPG widgets for this slot."""
        if self.row_tag and dpg.does_item_exist(self.row_tag):
            dpg.delete_item(self.row_tag)
        self.row_tag = None
