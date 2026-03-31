import dearpygui.dearpygui as dpg

from ..ui.slot_ui import SlotState, build_slot_row, build_add_slot_row, build_drop_gap


class SlotMixin:
    """Manages lineup slots: add, remove, reorder."""

    def add_initial_slots(self):
        self.refresh_slots()

    def _last_slot_duration(self) -> int:
        """Return the duration of the last slot, defaulting to 60."""
        if self.slots:
            try:
                return int(self.slots[-1].duration_var.get())
            except (ValueError, AttributeError):
                pass
        return 60

    def add_slot(self, name: str = "", genre: str = "", duration: int | None = None, index: int | None = None):
        if duration is None:
            duration = self._last_slot_duration()
        slot = SlotState(name, genre, duration)
        
        if index is not None:
            self.slots.insert(index, slot)
        else:
            self.slots.append(slot)
            
        self.refresh_slots()
        self.update_output()
        return slot

    def refresh_slots(self):
        """
        Delete and recreate all slot rows and drop gaps in the current order.
        Uses a clean-sweep approach to prevent 'ghost' widgets from blocking interactions.
        """
        parent = "slots_scroll"
        if not dpg.does_item_exist(parent):
            return

        # Clear the entire container. This is more robust than deleting by tag,
        # as it ensures no orphaned drop gaps or placeholders remain to block clicks.
        dpg.delete_item(parent, children_only=True)
            
        # Recreate in current order with gaps
        for i, slot in enumerate(self.slots):
            # Gap before the slot
            build_drop_gap(self, i, parent)
            # The slot itself
            build_slot_row(slot, self, parent)
            
        # Add the final drop gap at the very bottom
        build_drop_gap(self, len(self.slots), parent)
        
        # Add the '+ Add DJ Slot' button row
        build_add_slot_row(self, parent)

    def move_slot(self, slot_state: SlotState, direction: int):
        idx = self.slots.index(slot_state)
        new_idx = idx + direction
        if 0 <= new_idx < len(self.slots):
            self.slots[idx], self.slots[new_idx] = self.slots[new_idx], self.slots[idx]
            self.refresh_slots()
            self.update_output()

    def _duplicate_last_slot(self):
        if self.slots:
            s = self.slots[-1]
            try:
                dur = int(s.duration_var.get())
            except ValueError:
                dur = 60
            self.add_slot(s.name_var.get(), s.genre_var.get(), dur)

    def delete_slot(self, slot_state: SlotState):
        if slot_state in self.slots:
            # Note: slot_state.destroy() is called here but refresh_slots() 
            # will also clear the container, ensuring total cleanup.
            slot_state.destroy()
            self.slots.remove(slot_state)
            self.refresh_slots()
            self.update_output()