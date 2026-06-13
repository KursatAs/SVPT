bl_info = {
    "name": "SVPT",
    "author": "Kürşat ASLAN",
    "version": (1, 0),
    "blender": (5, 0, 0),
    "location": "View3D > N Panel > SVPT",
    "category": "3D View",
}

from .registration import register, unregister


if __name__ == "__main__":
    register()
