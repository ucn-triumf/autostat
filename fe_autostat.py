import midas
import midas.frontend
from PIDCtrlEquipment import *

class MyFrontend(midas.frontend.FrontendBase):
    """
    A frontend contains a collection of equipment.
    You can access self.client to access the ODB etc (see `midas.client.MidasClient`).
    """
    def __init__(self):
        # You must call __init__ from the base class.
        midas.frontend.FrontendBase.__init__(self, "fe_autostat")

        self.add_equipment(PIDCtrl_FPV212_TS245(self.client))
        self.add_equipment(PIDCtrl_FPV209_TS351(self.client))
        self.client.msg("AutoStat frontend initialized.")

    def frontend_exit(self):
        """
        Most people won't need to define this function, but you can use
        it for final cleanup if needed.
        """
        self.client.msg("AutoStat frontend stopped.")

if __name__ == "__main__":
    # The main executable is very simple - just create the frontend object,
    # and call run() on it.
    with MyFrontend() as my_fe:
        my_fe.run()
