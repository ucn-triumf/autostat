# He purifier runscripts
# Derek Fujimoto
# May 2025

import time
import collections
from CryoScript import CryoScript

class CryoScriptTester(CryoScript):
    # default settings
    DEFAULT_SETTINGS = collections.OrderedDict([
        ("temperature_K", 45),
        ("test", 150),
        ("test2", "a string"),
        ("timeout_s", 10),
        ('dry_run', False),
        ('wait_sleep_s', 60),
        ('wait_print_delay_s', 900),
        ("Enabled", False),
        ("_parnames", ["temperature_K", "test", "test2"]),
    ])
    def check_status(self):
        pass
    def run(self):
        time.sleep(2)
        print(self.settings['test2'], self.client.odb_get(f'{self.odb_settings_dir}/test2'))

