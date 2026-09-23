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

## help: Display this help message
help:
	@echo "$(BOLD)Extension : $(CYAN)$(EXT_ID)$(RESET) $(YELLOW)v$(VERSION)$(RESET) (Blender $(BLENDER_VER))"
	@echo ""
	@echo "$(BOLD)Available targets:$(RESET)"
	@echo "  $(GREEN)make build$(RESET)        - Build full .zip package (with bundled imageio-ffmpeg wheels)"
	@echo "  $(GREEN)make build-light$(RESET)  - Build lightweight .zip package (without wheels, uses system ffmpeg)"
	@echo "  $(GREEN)make install$(RESET)      - Build and install the .zip package into Blender (user_default)"
	@echo "  $(GREEN)make install-dev$(RESET)  - Create direct symlink in Blender for development (live reload)"
	@echo "  $(GREEN)make unlink$(RESET)       - Remove the development symlink"
	@echo "  $(GREEN)make uninstall$(RESET)    - Uninstall the extension from Blender"
	@echo "  $(GREEN)make wheels$(RESET)       - Download imageio-ffmpeg platform wheels into $(SRC_DIR)/wheels"
	@echo "  $(GREEN)make validate$(RESET)     - Validate $(SRC_DIR)/blender_manifest.toml with Blender CLI"
	@echo "  $(GREEN)make test$(RESET)         - Run automated test suite in headless Blender"
	@echo "  $(GREEN)make clean$(RESET)        - Remove build artifacts, .zip files, and Python cache files"
	@echo ""

## wheels: Download required imageio-ffmpeg platform wheels
wheels:
	@echo "$(CYAN)==> Downloading platform wheels into $(SRC_DIR)/wheels...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/download_wheels.py $(SRC_DIR)/wheels

## validate: Validate extension manifest
validate:
	@echo "$(CYAN)==> Validating $(SRC_DIR)/blender_manifest.toml...$(RESET)"
	@$(BLENDER) --command extension validate $(SRC_DIR)

## build: Build full .zip package (with bundled wheels)
build: validate
	@echo "$(CYAN)==> Building full extension package (with wheels)...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/build_package.py --output-dir $(BUILD_DIR)
	@echo "$(GREEN)==> Archive successfully created: $(ZIP_FILE)$(RESET)"

## build-light: Build lightweight .zip package (without wheels)
build-light: validate
	@echo "$(CYAN)==> Building lightweight extension package (without wheels)...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/build_package.py --light --output-dir $(BUILD_DIR)
	@echo "$(GREEN)==> Lightweight archive successfully created: $(ZIP_FILE)$(RESET)"

## install: Build and install into Blender
install: build
	@echo "$(CYAN)==> Installing $(PACKAGE_NAME) into Blender (user_default)...$(RESET)"
	@$(BLENDER) --command extension install-file -r user_default --enable $(ZIP_FILE)
	@echo "$(GREEN)==> Extension successfully installed and enabled in Blender!$(RESET)"

## install-dev / link: Install via symbolic link for live development
install-dev: link

link:
	@echo "$(CYAN)==> Configuring development symbolic link...$(RESET)"
	@mkdir -p $(USER_EXT_DIR)
	@ln -sfn $(CURDIR)/$(SRC_DIR) $(DEV_LINK)
	@echo "$(GREEN)==> Symbolic link created:$(RESET)"
	@echo "    $(DEV_LINK) -> $(CURDIR)/$(SRC_DIR)"
	@echo "$(YELLOW)Tip: Restart Blender or press 'F3 > Reload Scripts' to see live changes.$(RESET)"

## unlink: Remove development symbolic link
unlink:
	@if [ -L "$(DEV_LINK)" ]; then \
		rm -f "$(DEV_LINK)"; \
		echo "$(GREEN)==> Development symbolic link removed: $(DEV_LINK)$(RESET)"; \
	else \
		echo "$(YELLOW)==> No symbolic link to remove in $(USER_EXT_DIR)$(RESET)"; \
	fi

## uninstall: Uninstall extension from Blender
uninstall: unlink
	@echo "$(CYAN)==> Removing extension via Blender CLI...$(RESET)"
	@-$(BLENDER) --command extension remove $(EXT_ID) 2>/dev/null || true
	@echo "$(GREEN)==> Extension uninstalled.$(RESET)"

## test: Run automated headless tests in Blender
test:
	@echo "$(CYAN)==> Running test suite with Blender $(BLENDER_VER)...$(RESET)"
	@$(BLENDER) --background --python $(TESTS_DIR)/test_addon.py

## clean: Clean generated files and caches
clean:
	@echo "$(CYAN)==> Cleaning up...$(RESET)"
	@rm -rf $(BUILD_DIR) *.zip
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
	@echo "$(GREEN)==> Clean complete.$(RESET)"
