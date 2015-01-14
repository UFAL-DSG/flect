SHELL := bash

DATA_DIR   := data
RUNS_DIR   := runs
TRY_NUM    := $(shell perl -e '$$m=0; for(<$(RUNS_DIR)/*>){/\/(\d+)_/ and $$1 > $$m and $$m=$$1;} printf "%03d", $$m+1;')
LAST_NUM   := $(shell ls -d -r $(RUNS_DIR)/[0-9]* 2>/dev/null | head -n 1 | sed 's/^[^\/]*\/\([0-9]*\)_.*/\1/')
LAST_DIR   := $(shell ls -d -r $(RUNS_DIR)/$(LAST_NUM)* 2>/dev/null | head -n 1)

DATE       := $(shell date +%Y-%m-%d_%H-%M-%S)
TRY_DIR     = $(RUNS_DIR)/$(TRY_NUM)_$(DATE)_$(SHORT_DESC)

DESC       :=
ifdef D # Shortcut D -> DESC
  DESC := $(D)
endif
SHORT_DESC = $(shell echo "$(DESC)" | sed 's/runs\/\([0-9]*\)[^\/]*\//\1-/g;s/\.pickle\.gz//g;s/[^\.A-Za-z0-9-]/_/g' | sed 's/_\+/_/g;s/\(.*\)/\L\1/;' )

DATA_ID =
ifneq ($(DATA),)
  DATA_ID = -$(DATA)
endif
ifneq ($(LANG),)
  LANG_ID = $(LANG)_
endif

ifneq ($(ANOT),)
  ANOT_SW=-a
  ANOT_SUF=-annot
endif

ifneq ($(TPART),)
  TPART_SPEC=$(TPART):
endif

ifneq ($(MEM),)
  MEM_SPEC=-m $(MEM)
endif



SET=dtest

SRC_ATTR=Lemma
TRG_ATTR=Form
POS_ATTR=Tag_POS

define HELP_MESSAGE
# Flect training
# --------------
# This makefile automates and simplifies experiments with training Flect models.
# The experiments are saved in $(RUNS_DIR)/ and numbered consecutively.
# There are the following commands available:
#
# Run training (take data from data/, use runs/, use config from run ###;
# the default config from flect/configs/config_$$LANG.py is used if CONFIG is unset)
make train D="Description" DATA="data_id" [CONFIG=###] [LANG=cs] [MEM=32]
# Print scores for run ### (can be limited to top ##):
make scores-### [BEST=##]
# Print the highest core for run ###
make highscore-###
# List previous experiments
make desc
# List available data sets for training
make list-data
# create one data set from multiple .arff files
make create DATA="data_id" SET=(train|dtest|etest) IN_DIR=/input/directory
# apply given models to a test set and measure performance
make test M1=path/model1.pickle.gz [M2=...] DATA="data_id" [SET=etest] [TPART=0.XX]
# save an ARFF file with the errors of the best model from the given run
make errors-### [ANOT=1]
endef
export HELP_MESSAGE

help:
	@echo "$$HELP_MESSAGE" | egrep --color '^(make.*|)'


prepare_dir:
	@if [ -z "$(DESC)" ]; then \
		echo "Empty description. Aborting." \
		exit 1; \
	fi ;
	# create the directory
	mkdir -p $(TRY_DIR)
	# print descriptions	
	echo "$(DESC)" > $(TRY_DIR)/ABOUT
	echo "LANG: $(LANG)" >>  $(TRY_DIR)/ABOUT
	echo "DATA: $(DATA)" >>  $(TRY_DIR)/ABOUT

prepare_config:
	@if [ -z "$(CONFIG)" ]; then \
		cp ../../configs/config_$(LANG).py $(TRY_DIR)/config.py ;\
	else \
		cp $(RUNS_DIR)/$(CONFIG)*/config.py $(TRY_DIR)/ ;\
	fi
	$(EDITOR) $(TRY_DIR)/config.py

train: prepare_dir prepare_config
	../../bin/train.py -n t$(TRY_NUM) $(MEM_SPEC) $(TRY_DIR) config.py $(DATA_DIR)/$(LANG_ID)train$(DATA_ID).arff.gz model.pickle.gz $(DATA_DIR)/$(LANG_ID)$(SET)$(DATA_ID).arff.gz classif.arff.gz | tee $(TRY_DIR)/output.log

train_split: prepare_dir prepare_config
	../../bin/train.py -l -n t$(TRY_NUM) $(MEM_SPEC) $(TRY_DIR) config.py '$(DATA_DIR)/$(LANG)-$(DATA)/train-*.arff.gz' 'model-*.pickle.gz' | tee $(TRY_DIR)/output.log
	# for TRAIN_FILE in $(DATA_DIR)/$(LANG)-$(DATA)/train-*.arff.gz; do \
		    #FILE_ID=`echo $$TRAIN_FILE | sed 's/.*train-//;s/\.arff\.gz//;'`; \
		#if [ -e $(DATA_DIR)/$(LANG)-$(ID)/$(SET)-$$FILE_ID.arff.gz ]; then \
			      #../../bin/train.py -n t$(TRY_NUM)-$$FILE_ID $(MEM_SPEC) $(TRY_DIR) config.py $$TRAIN_FILE model-$$FILE_ID.pickle.gz $(DATA_DIR)/$(LANG)-$(ID)/$(SET)-$$FILE_ID.arff.gz classif-$$FILE_ID.arff.gz | tee -a $(TRY_DIR)/output.log ; \
		#else \
			#../../bin/train.py -n t$(TRY_NUM)-$$FILE_ID $(MEM_SPEC) $(TRY_DIR) config.py $$TRAIN_FILE model-$$FILE_ID.pickle.gz | tee -a $(TRY_DIR)/output.log ; \
		#fi; \
	#done


test: DESC = Test: $(M1) $(M2) $(M3) $(M4) $(M5) (Set: $(SET))
test: prepare_dir
	@MODELS=""; \
	for M in $(M1) $(M2) $(M3) $(M4) $(M5); do \
		MODELS="$$MODELS -m $$M" ; \
	done; \
	../../bin/test.py -s $(SRC_ATTR) -t $(TRG_ATTR) -i -p $(POS_ATTR) -o $(TPART_SPEC)$(DATA_DIR)/$(LANG_ID)train$(DATA_ID).arff.gz $$MODELS $(DATA_DIR)/$(LANG_ID)$(SET)$(DATA_ID).arff.gz $(TRY_DIR)/classif.arff.gz 2>&1 | tee $(TRY_DIR)/output.log

scores-%:
	@make $(@:-$*=) LAST_NUM=$* BEST=$(BEST)

highscore-%:
	@make scores LAST_NUM=$* BEST=1

scores:
	@if [ -n '$(BEST)' ]; then \
		grep 'Score' $(LAST_DIR)/*.py.o* $(LAST_DIR)/output.log 2> /dev/null | sort -t ':' -k 5 | sed 's/Score/\tScore/' | tail -n $(BEST) ; \
	else \
		grep 'Score' $(LAST_DIR)/*.py.o* $(LAST_DIR)/output.log 2> /dev/null | sort -t ':' -k 5 | sed 's/Score/\tScore/' ; \
	fi

desc:
	@ls $(RUNS_DIR)/*/ABOUT | sort | while read file; do echo -ne $$file ": \t" | sed 's/$(RUNS_DIR)\///g;s/_\([a-z][^\/]*\)\?\/ABOUT//;'; cat $$file | sed 's/runs\/\([0-9]*\)[^\/]*\//\1-/g;s/\.pickle\.gz//g;' | tr '\n' '\t'; echo; done


list-data:
	@ls $(DATA_DIR)/$(LANG_ID)train*.arff.gz | sed 's/.*train-//;/train\./s/^.*$$/(default)/;s/\.arff\.gz//;'

create:
	cat $(IN_DIR)/*.arff | sed '50,$$s/^@ATTRIBUTE.*$$//;50,$$s/^@RELATION.*$$//;50,$$s/^@DATA.*$$//;/^$$/d;' | gzip -c > $(DATA_DIR)/$(LANG_ID)$(SET)-$(DATA).arff.gz

errors-%:
	@make $(@:-$*=) LAST_NUM=$* ANOT=$(ANOT)

errors: runs/best-$(LAST_NUM)-errors$(ANOT_SUF).arff.gz
	vi runs/best-$(LAST_NUM)-errors$(ANOT_SUF).arff.gz

runs/best-$(LAST_NUM)-errors$(ANOT_SUF).arff.gz:
	BEST=`make highscore-$(LAST_NUM) | grep -v '^make' | sed 's/.*t[0-9]\+-\([^\.]*\)\.py.*/\1/'`; \
	TARGET=`grep 'class_attr' runs/$(LAST_NUM)*/config.py | sed "s/.*class_attr.*:.*'\([^']*\)'.*/\1/"`; \
	../../bin/select_errors.py $(ANOT_SW) -g $$TARGET runs/$(LAST_NUM)*/classif-t$(LAST_NUM)-$$BEST.arff.gz runs/best-$(LAST_NUM)-errors$(ANOT_SUF).arff.gz ; \

