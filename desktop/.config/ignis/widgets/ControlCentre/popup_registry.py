from widgets.ControlCentre.widget import ControlCentrePopup

class PopupRegistry:
    def __init__(self):
        self.popups: list[ControlCentrePopup] = []

    def register(self, popup: ControlCentrePopup):
        if popup not in self.popups:
            self.popups.append(popup)

    def close_all(self):
        for p in self.popups:
            p.set_reveal_child(False)

    def close_all_but(self, except_popup: ControlCentrePopup | None):
        for p in self.popups:
            if p is not except_popup:
                p.set_reveal_child(False)

popup_registry = PopupRegistry()
