import os
import platform

if platform.system() == "Linux":
    os.environ.setdefault("PYOPENGL_PLATFORM", "glx")
