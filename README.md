# SVPT

SVPT is a Blender 3D View add-on designed to make zooming more reliable while sculpting from reference images.

When sculpting with reference images, one common problem is that normal viewport or camera zoom can change the perceived perspective of the model. As the artist zooms in or out, the relationship between the sculpt and the reference image may appear to shift. This can make proportions, silhouette, volume, and surface forms look different than they actually are.

SVPT aims to reduce that issue by keeping the perspective feel as stable as possible during zoom. It uses lens-aware zoom behavior instead of only changing viewport distance, helping the artist inspect details without constantly disturbing the visual match between the model and the reference.

The main purpose of SVPT is not just smoother navigation. Its purpose is to support reference-based sculpting by minimizing misleading perspective changes during zoom.

## What SVPT Helps With

- Sculpting from reference images with more stable visual perception
- Reducing perspective changes caused by normal viewport zoom
- Comparing model proportions against references while zooming
- Inspecting details without strongly changing the apparent form
- Saving and restoring important sculpting views

## Features

- Perspective-stable zoom behavior for reference-based sculpting
- Lens/FOV-based zoom mode
- Optional camera-backed lens zoom
- Mouse pivot zoom around the surface under the cursor
- Smooth scroll inertia
- Modifier-based zoom speed control
- Continuous drag zoom gestures
- Scene-persistent view bookmarks
- Viewport HUD for lens, distance, backend, pivot, and zoom state

## Requirements

- Blender 5.0.0 or newer

## Installation

Install SVPT as a Blender add-on or extension.

For a local add-on install:

1. Place the `SVPT` folder in Blender's add-ons directory.
2. Open Blender.
3. Go to `Edit > Preferences > Add-ons`.
4. Search for `SVPT`.
5. Enable the add-on.

The panel appears in:

```text
3D View > Sidebar / N Panel > SVPT
```

## Usage

Open the 3D View sidebar with `N`, then select the `SVPT` tab.

Enable `SVPT` to activate the custom zoom behavior.

## Controls

SVPT registers the following 3D View key bindings:

| Input | Action |
| --- | --- |
| Mouse Wheel Up / Down | Zoom in / out |
| Ctrl + Mouse Wheel | Faster zoom |
| Shift + Mouse Wheel | Slower zoom |
| Ctrl + Shift + Mouse Wheel | Faster zoom |
| Numpad Plus / Minus | Zoom in / out |
| Ctrl + Middle Mouse Drag | Continuous zoom |
| Ctrl + Shift + Middle Mouse Drag | Continuous zoom |
| Alt + Right Mouse Drag | Continuous zoom |

## Panel Options

### Enabled

Turns SVPT zoom behavior on or off.

When enabled, SVPT stores the current lens and view distance. When disabled, it restores the saved lens and distance.

### Lens Zoom

Uses lens/FOV-based zoom instead of simple distance zoom.

This creates a steadier perspective zoom feel. SVPT internally supports lens values beyond Blender's normal 250 mm viewport lens limit by combining lens changes with view-distance adjustment.

When disabled, SVPT uses dolly-style zoom by changing viewport distance and view location.

### Lens Zoom Backend

Controls how lens zoom is applied.

#### Viewport

Uses the active 3D View lens and view distance.

This is the default backend and works directly in the viewport.

#### Scene Camera

Creates or reuses an internal camera named `SVPT_Temp_Camera` inside a collection named `SVPT Camera`.

SVPT switches the active 3D View to camera view, enables local camera behavior for that viewport, locks the camera to the view, and applies zoom through the camera lens.

When the camera backend is disabled, SVPT restores the previous scene camera, local camera, camera lock, and view perspective state.

### Mouse Pivot

When enabled, SVPT raycasts under the mouse cursor and zooms around the hit point.

If no surface is found under the cursor, SVPT falls back to the current view location.

### Smooth Scroll

Adds inertia to mouse wheel zoom.

When disabled, wheel zoom is applied instantly.

### Manual Lens

Lets you directly set the viewport lens while SVPT is enabled.

This control is mainly intended to show and adjust the visible focal length value while SVPT is active. It is not the most reliable way to define the starting focal length for a session.

For more predictable behavior, set the desired viewport focal length manually from Blender's N panel before enabling SVPT.

## View Bookmarks

SVPT can save and restore viewport states from the panel.

Each bookmark stores:

- Name
- Lens
- View distance
- View location
- View rotation
- View perspective
- View matrix
- SVPT enabled state
- Lens zoom state
- Lens zoom backend
- Camera matrix when using the camera backend

Bookmarks are stored on the current Blender scene, so they are saved with the `.blend` file.

### Bookmark Actions

Use the bookmark controls in the SVPT panel:

| Button | Action |
| --- | --- |
| Plus | Save the current view as a bookmark |
| Minus | Remove the selected bookmark |
| Selecting a bookmark | Restores that bookmarked view |

## HUD

SVPT draws a small HUD in the 3D View showing:

- SVPT on/off state
- Current lens
- Current view distance
- Lens zoom state
- Active backend
- Mouse pivot state
- Smooth scroll state
- Zoom percentage

HUD options are available in the add-on preferences:

- HUD X position
- HUD Y position
- Show zoom percentage

## Technical Notes

SVPT registers settings on `WindowManager`:

```python
window_manager.svpt_settings
```

View bookmarks are stored on `Scene`:

```python
scene.svpt_view_bookmarks
```

The add-on registers a viewport draw handler for the HUD and removes it during unregister.

When using the camera backend, SVPT creates a temporary camera object if one does not already exist. The camera is hidden again when the backend is deactivated.

## Files

| File | Purpose |
| --- | --- |
| `__init__.py` | Blender add-on metadata and register/unregister entry point |
| `registration.py` | Class registration, keymaps, HUD draw handler setup |
| `operators.py` | Zoom, drag zoom, scroll zoom, and bookmark operators |
| `properties.py` | Add-on settings and bookmark data structures |
| `ui.py` | SVPT sidebar panel and bookmark UI list |
| `utils.py` | Viewport helpers, mouse pivot raycast, camera backend helpers |
| `hud.py` | Viewport HUD drawing |
| `preferences.py` | Add-on preferences for HUD placement and zoom percentage |
| `state.py` | Runtime state dictionary |
| `constants.py` | Zoom limits and speed multipliers |
| `blender_manifest.toml` | Blender extension manifest |

## License

GPL-3.0-or-later
