from ..utils import settings

import os
import shutil


class Dependencies:
    def __init__(self, parent):
        self.required = settings.pull("-install/required")
        self.parent = parent

    def check_existence(self):
        required = []

        for v in self.required:
            v = settings.pull(v)
            if not shutil.which(v):
                required.append(os.path.basename(v))

        if required:
            self.parent.element("msg.pop")(f"requirements: {tuple(required)} not found ! "
                                           f"some functions wouldn't work properly .")
