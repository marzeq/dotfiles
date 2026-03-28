from widgets.ControlCentre.widget import ControlCentrePopup
import weakref


class PopupRegistry:
    def __init__(self):
        self.popups: weakref.WeakSet[ControlCentrePopup] = weakref.WeakSet()

    def register(self, popup: ControlCentrePopup):
        self.popups.add(popup)

    def close_all(self):
        for p in self.popups:
            p.set_reveal_child(False)

    def close_all_but(self, except_popup: ControlCentrePopup | None):
        for p in self.popups:
            if p is not except_popup:
                p.set_reveal_child(False)


popup_registry = PopupRegistry()
