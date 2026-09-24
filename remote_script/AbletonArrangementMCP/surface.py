import json
import os
import Live
from _Framework.ControlSurface import ControlSurface
from .api import ArrangementAPI
from .transport import JSONTCPBridge


class ArrangementSurface(ControlSurface):
    def __init__(self, c_instance):
        super(ArrangementSurface, self).__init__(c_instance)
        self._bridge = None
        try:
            with open(os.path.join(os.path.dirname(__file__), "config.json"), encoding="utf-8") as file:
                config = json.load(file)
            application = Live.Application.get_application()
            version = "%s.%s.%s" % (application.get_major_version(), application.get_minor_version(),
                                    application.get_bugfix_version())
            self._api = ArrangementAPI(self.song(), version, getattr(Live.Clip, "MidiNoteSpecification", None))
            port = config.get("port", 8765)
            if type(port) is not int or not 1024 <= port <= 65535:
                raise ValueError("port must be between 1024 and 65535")
            self._bridge = JSONTCPBridge(self._api.call, config["token"], port)
            self.log_message("Arrangement MCP: listening on 127.0.0.1:%s" % port)
            self.show_message("Arrangement MCP ready (Live %s)" % version)
        except Exception as exc:
            self.log_message("Arrangement MCP startup failed: %s" % exc)
            self.show_message("Arrangement MCP: check config.json and Live Log.txt")

    def update_display(self):
        super(ArrangementSurface, self).update_display()
        if self._bridge is not None:
            self._bridge.poll()

    def disconnect(self):
        if self._bridge is not None:
            self._bridge.close()
            self._bridge = None
        super(ArrangementSurface, self).disconnect()
