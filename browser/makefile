
all:	vue.config.js prod deploy

# ------------------------------------------------
ifeq ($(shell hostname),ASDI-DB)

vue.config.js:
	@cp cssi.config.js vue.config.js
	echo "asdi config"

deploy:
	echo "no need for separate deploy step on asdi-db"

endif

# ------------------------------------------------
ifeq ($(shell hostname),acy_test_app_vm_rserver)

vue.config.js:
	@cp faa.config.js vue.config.js
	echo "faa config"

deploy:
	@echo "now do this (NOTE: TEST):"
	@echo "   cd ../rs_deploy; ./deploy_me.sh test ; cd ../browser"
	@echo "and visit the connect page (allows login):"
	@echo "   http://172.26.21.40:3939/connect/#/apps/201"
	@echo "or the external page (no login):"
	@echo "   http://172.26.21.40:3939/content/201/"

endif

# ------------------------------------------------

prod: vue.config.js
	npm run-script build

dev: vue.config.js
	npm run-script mydev

#clean:
#	-rm    rs_deploy/templates/index.html 
#	-rm -r rs_deploy/static/*

reallyclean: # clean
	-rm vue.config.js
	-rm -r node_modules/*
	-rm -r node_modules/.bin
	-rm -r node_modules/.cache

