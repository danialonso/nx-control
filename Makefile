# NX Control - top level build
VERSION ?= 0.0.0-dev
PROGRAM_ID := 4200000000004E58

.PHONY: all sysmodule overlay app dist clean

all: sysmodule overlay app

sysmodule:
	$(MAKE) -C sysmodule APP_VERSION=$(VERSION)

overlay:
	$(MAKE) -C overlay APP_VERSION=$(VERSION)

app:
	$(MAKE) -C app APP_VERSION=$(VERSION)

dist: all
	rm -rf dist
	mkdir -p dist/sd/atmosphere/contents/$(PROGRAM_ID)/flags
	mkdir -p dist/sd/switch/nxcontrol dist/sd/switch/.overlays
	cp sysmodule/nxcontrol.nsp dist/sd/atmosphere/contents/$(PROGRAM_ID)/exefs.nsp
	cp sysmodule/toolbox.json   dist/sd/atmosphere/contents/$(PROGRAM_ID)/toolbox.json
	touch dist/sd/atmosphere/contents/$(PROGRAM_ID)/flags/boot2.flag
	cp app/nxcontrol.nro        dist/sd/switch/nxcontrol/nxcontrol.nro
	cp overlay/nxcontrol.ovl    dist/sd/switch/.overlays/nxcontrol.ovl
	cp -r dist-template/config  dist/sd/
	cd dist/sd && zip -r ../NX-Control-$(VERSION).zip .

clean:
	$(MAKE) -C sysmodule clean
	$(MAKE) -C overlay clean
	$(MAKE) -C app clean
	rm -rf dist
