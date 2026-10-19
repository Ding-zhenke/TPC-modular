"""Shared lazy CST-session access for topology device templates."""


class TopologyTemplate:
    @property
    def app(self):
        """Resolve the CST application only when a CST-backed action needs it."""
        return self.modeler.app

    @app.setter
    def app(self, value):
        # Preserve legacy test/script injection while keeping construction offline.
        self.modeler.app = value
