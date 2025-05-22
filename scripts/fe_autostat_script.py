import midas
import midas.frontend
import logging
from logging.handlers import RotatingFileHandler

import he_purifier
import CryoScriptSequencer

class MyFrontend(midas.frontend.FrontendBase):
    """
    A frontend contains a collection of equipment.
    You can access self.client to access the ODB etc (see `midas.client.MidasClient`).
    """
    def __init__(self):
        # You must call __init__ from the base class.
        midas.frontend.FrontendBase.__init__(self, "fe_autostat_script")

        # make logger --------------------------------------------------------
        logger = logging.getLogger('fe_autostat_script')
        logger.setLevel(logging.INFO)
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        # setup file handler with rotating file handling
        rfile_handler = RotatingFileHandler(f'fe_autostat_script.log', mode='a',
                                            maxBytes=5*1024*1024, backupCount=1,
                                            encoding=None, delay=False)
        rfile_handler.setFormatter(log_formatter)
        rfile_handler.setLevel(logging.INFO)

        # only add handler if it doesn't exist already
        add_handler = True
        for handler in logger.handlers:
            if handler.baseFilename == rfile_handler.baseFilename:
                add_handler = False
                break

        if add_handler:
            logger.addHandler(rfile_handler)

        # add equipment ------------------------------------------------------

        # from he_purifier
        self.add_equipment(CryoScriptSequencer.CryoScriptSequencer(self.client))
        self.add_equipment(he_purifier.StartCooling(self.client, logger))
        self.add_equipment(he_purifier.StopCooling(self.client, logger))
        # self.add_equipment(he_purifier.StartCirculation(self.client, logger))
        self.add_equipment(he_purifier.StopCirculation(self.client, logger))
        self.add_equipment(he_purifier.StartRecovery(self.client, logger))
        self.add_equipment(he_purifier.StopRecovery(self.client, logger))
        self.add_equipment(he_purifier.StartRegeneration(self.client, logger))
        self.add_equipment(he_purifier.StopRegeneration(self.client, logger))

        # test
        # self.add_equipment(he_purifier.CryoScriptTester(self.client, logger))


        self.client.msg("AutoStat Scripting frontend initialized.")

    def frontend_exit(self):
        """
        You MAY implement this function in your dervived class.

        To GUARANTEE that this function gets called, you should use a context
        manager style for the frontend class (`with` syntax).

        ```
        # This style will work in most cases, but is not guaranteed to call
        # `frontend_exit()` when the program exits (depends on your specific
        # python version/implementation and python code):
        my_fe = MyFrontend("my_fe")
        my_fe.run()

        # This style is guaranteed to call `frontend_exit()`:
        with MyFrontend("my_fe") as my_fe:
            my_fe.run()
        ```
        """
        self.client.msg("AutoStat Scripting frontend stopped.")

if __name__ == "__main__":
    # The main executable is very simple - just create the frontend object,
    # and call run() on it.
    with MyFrontend() as my_fe:
        my_fe.run()
