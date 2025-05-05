import midas
import midas.frontend
import PIDCtrlEquipment
import PIDCtrlPurifier
import PIDCtrlTailHTRs

class MyFrontend(midas.frontend.FrontendBase):
    """
    A frontend contains a collection of equipment.
    You can access self.client to access the ODB etc (see `midas.client.MidasClient`).
    """
    def __init__(self):
        # You must call __init__ from the base class.
        midas.frontend.FrontendBase.__init__(self, "fe_autostat_pid")

        # from PIDCtrlEquipment
        self.add_equipment(PIDCtrlEquipment.PIDCtrl_FPV205_TS505(self.client))
        self.add_equipment(PIDCtrlEquipment.PIDCtrl_FPV206_TS525(self.client))
        self.add_equipment(PIDCtrlEquipment.PIDCtrl_FPV207_TS508(self.client))
        self.add_equipment(PIDCtrlEquipment.PIDCtrl_FPV209_TS351(self.client))
        self.add_equipment(PIDCtrlEquipment.PIDCtrl_FPV212_TS245(self.client))

        # from PIDCtrlPurifier
        self.add_equipment(PIDCtrlPurifier.PIDCtrl_HTR105_TS510(self.client))
        self.add_equipment(PIDCtrlPurifier.PIDCtrl_HTR010_TS512(self.client))
        self.add_equipment(PIDCtrlPurifier.PIDCtrl_HTR107_TS511(self.client))
        self.add_equipment(PIDCtrlPurifier.PIDCtrl_HTR012_TS513(self.client))

        # from PIDCtrlTailHTRs
        self.add_equipment(PIDCtrlTailHTRs.PIDCtrl_HTR001(self.client))
        self.add_equipment(PIDCtrlTailHTRs.PIDCtrl_HTR003(self.client))
        self.add_equipment(PIDCtrlTailHTRs.PIDCtrl_HTR004(self.client))
        self.add_equipment(PIDCtrlTailHTRs.PIDCtrl_HTR005(self.client))
        self.add_equipment(PIDCtrlTailHTRs.PIDCtrl_HTR006(self.client))
        self.add_equipment(PIDCtrlTailHTRs.PIDCtrl_HTR007(self.client))
        self.add_equipment(PIDCtrlTailHTRs.PIDCtrl_HTR008(self.client))

        self.client.msg("AutoStat PID frontend initialized.")

    def frontend_exit(self):
        """
        Most people won't need to define this function, but you can use
        it for final cleanup if needed.
        """
        self.client.msg("AutoStat PID frontend stopped.")

if __name__ == "__main__":
    # The main executable is very simple - just create the frontend object,
    # and call run() on it.
    with MyFrontend() as my_fe:
        my_fe.run()
