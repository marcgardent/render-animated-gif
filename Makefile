# ==============================================================================
# Makefile for Render Animated Image (GIF & WebP) Blender Extension
# ==============================================================================

BLENDER      ?= blender
PYTHON       ?= python3

SRC_DIR      := src
TESTS_DIR    := tests
SCRIPTS_DIR  := scripts

# Extension metadata from src/blender_manifest.toml
EXT_ID       := $(shell grep '^id\s*=' $(SRC_DIR)/blender_manifest.toml | cut -d'"' -f2)
VERSION      := $(shell grep '^version\s*=' $(SRC_DIR)/blender_manifest.toml | cut -d'"' -f2)
PACKAGE_NAME := $(EXT_ID)-$(VERSION).zip

BUILD_DIR    := build
ZIP_FILE     := $(BUILD_DIR)/$(PACKAGE_NAME)

# Detect Blender version (e.g., 5.2 or 4.2)
BLENDER_VER  := $(shell $(BLENDER) --version 2>/dev/null | head -n 1 | cut -d' ' -f2 | cut -d. -f1,2)

# Blender extension directories
USER_EXT_DIR := $(HOME)/.config/blender/$(BLENDER_VER)/extensions/user_default
DEV_LINK     := $(USER_EXT_DIR)/$(EXT_ID)

# Colors for terminal output
BOLD         := \033[1m
GREEN        := \033[0;32m
CYAN         := \033[0;36m
YELLOW       := \033[0;33m
RED          := \033[0;31m
RESET        := \033[0m

.PHONY: all help build build-light install install-dev link unlink uninstall wheels validate test clean

all: help

## help: Afficher cette aide
help:
	@echo "$(BOLD)Extension : $(CYAN)$(EXT_ID)$(RESET) $(YELLOW)v$(VERSION)$(RESET) (Blender $(BLENDER_VER))"
	@echo ""
	@echo "$(BOLD)Cibles disponibles :$(RESET)"
	@echo "  $(GREEN)make build$(RESET)        - Construit le package .zip complet (avec wheels imageio-ffmpeg)"
	@echo "  $(GREEN)make build-light$(RESET)  - Construit un package .zip léger (sans wheels, utilise ffmpeg système)"
	@echo "  $(GREEN)make install$(RESET)      - Construit et installe le package .zip dans Blender (user_default)"
	@echo "  $(GREEN)make install-dev$(RESET)  - Crée un lien symbolique direct dans Blender pour le développement (live reload)"
	@echo "  $(GREEN)make uninstall$(RESET)    - Désinstalle l'extension de Blender et supprime le lien de dev"
	@echo "  $(GREEN)make wheels$(RESET)       - Télécharge les wheels de plateforme imageio-ffmpeg dans $(SRC_DIR)/wheels"
	@echo "  $(GREEN)make validate$(RESET)     - Valide le fichier $(SRC_DIR)/blender_manifest.toml"
	@echo "  $(GREEN)make test$(RESET)         - Lance les tests automatisés dans Blender en arrière-plan"
	@echo "  $(GREEN)make clean$(RESET)        - Supprime le dossier build/, les archives .zip et les fichiers temporaires"
	@echo ""

## wheels: Télécharger les wheels imageio-ffmpeg requis pour l'archive complète
wheels:
	@echo "$(CYAN)==> Téléchargement des wheels plateformes dans $(SRC_DIR)/wheels...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/download_wheels.py $(SRC_DIR)/wheels

## validate: Valider le manifeste de l'extension
validate:
	@echo "$(CYAN)==> Validation de $(SRC_DIR)/blender_manifest.toml...$(RESET)"
	@$(BLENDER) --command extension validate $(SRC_DIR)

## build: Construire le package complet .zip
build: validate
	@echo "$(CYAN)==> Construction du package complet (avec wheels)...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/build_package.py --output-dir $(BUILD_DIR)
	@echo "$(GREEN)==> Archive créée avec succès : $(ZIP_FILE)$(RESET)"

## build-light: Construire le package léger .zip sans wheels
build-light: validate
	@echo "$(CYAN)==> Construction du package léger (sans wheels)...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/build_package.py --light --output-dir $(BUILD_DIR)
	@echo "$(GREEN)==> Archive légère créée avec succès : $(ZIP_FILE)$(RESET)"

## install: Construire et installer dans Blender
install: build
	@echo "$(CYAN)==> Installation de $(PACKAGE_NAME) dans Blender (user_default)...$(RESET)"
	@$(BLENDER) --command extension install-file -r user_default --enable $(ZIP_FILE)
	@echo "$(GREEN)==> Extension installée et activée avec succès dans Blender !$(RESET)"

## install-dev / link: Installer via lien symbolique pour le développement
install-dev: link

link:
	@echo "$(CYAN)==> Configuration du lien symbolique de développement...$(RESET)"
	@mkdir -p $(USER_EXT_DIR)
	@ln -sfn $(CURDIR)/$(SRC_DIR) $(DEV_LINK)
	@echo "$(GREEN)==> Lien symbolique créé :$(RESET)"
	@echo "    $(DEV_LINK) -> $(CURDIR)/$(SRC_DIR)"
	@echo "$(YELLOW)Conseil : Relancez Blender ou faites 'F3 > Reload Scripts' pour voir les modifications en direct.$(RESET)"

## unlink: Supprimer le lien symbolique de dev
unlink:
	@if [ -L "$(DEV_LINK)" ]; then \
		rm -f "$(DEV_LINK)"; \
		echo "$(GREEN)==> Lien symbolique de développement supprimé : $(DEV_LINK)$(RESET)"; \
	else \
		echo "$(YELLOW)==> Aucun lien symbolique à supprimer dans $(USER_EXT_DIR)$(RESET)"; \
	fi

## uninstall: Désinstaller de Blender
uninstall: unlink
	@echo "$(CYAN)==> Suppression de l'extension via Blender CLI...$(RESET)"
	@-$(BLENDER) --command extension remove $(EXT_ID) 2>/dev/null || true
	@echo "$(GREEN)==> Extension désinstallée.$(RESET)"

## test: Lancer les tests automatisés dans Blender
test:
	@echo "$(CYAN)==> Exécution de la suite de tests avec Blender $(BLENDER_VER)...$(RESET)"
	@$(BLENDER) --background --python $(TESTS_DIR)/test_addon.py

## clean: Nettoyer les fichiers générés
clean:
	@echo "$(CYAN)==> Nettoyage...$(RESET)"
	@rm -rf $(BUILD_DIR) *.zip
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
	@echo "$(GREEN)==> Nettoyage terminé.$(RESET)"
