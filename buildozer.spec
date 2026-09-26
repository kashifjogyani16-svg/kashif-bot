[app]
title = Kashif Master Bot
package.name = kashifbot
package.domain = org.kashif
source.dir = .
source.include_exts = py,txt,png,jpg,kv,atlas,json
version = 1.0

requirements = python3,kivy==2.2.1,requests,urllib3,certifi,chardet,idna,fake-useragent==1.4.0,plyer,android

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
