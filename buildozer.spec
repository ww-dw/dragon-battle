[app]
title = Dragon Feast
package.name = dragonfeast
package.domain = org.wuyang.dragonfeast
source.dir = src
source.include_exts = py
version = 1.0
author = 吴恙

requirements = python3,pygame

orientation = landscape
fullscreen = 1

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
android.features = android.hardware.touchscreen.multitouch.distinct
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
