#!/usr/bin/env bash
# ==============================================================================
# WikiGPT Installer
# Sets up dependencies, configures the Gemini API Key, and adds wikigpt to PATH.
# ==============================================================================

set -e

# Styling
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${BLUE}"
echo "==========================================================="
echo "   📚 WikiGPT Installer & Setup Assistant"
echo "==========================================================="
echo -e "${RESET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIKIGPT_SRC="$SCRIPT_DIR/wikigpt.py"

if [ ! -f "$WIKIGPT_SRC" ]; then
    echo -e "${RED}❌ Error: Could not find wikigpt.py in $SCRIPT_DIR${RESET}"
    exit 1
fi

# ------------------------------------------------------------------------------
# 1. Check Python 3 and Pip
# ------------------------------------------------------------------------------
echo -e "${BOLD}[1/4] Checking Python environment...${RESET}"

if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌ Error: python3 is not installed or not in your PATH.${RESET}"
    echo "Please install Python 3.9+ using your package manager (e.g. apt install python3, brew install python3)."
    exit 1
fi

PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo -e "${GREEN}✓ Found Python $PY_VER${RESET}"

echo -e "Checking Python packages ('google-genai', 'certifi')..."
if python3 -c "import google.genai, certifi" &>/dev/null; then
    echo -e "${GREEN}✓ Required packages are already installed.${RESET}"
else
    echo -e "${YELLOW}Installing required dependencies via pip...${RESET}"
    if command -v pip3 &>/dev/null; then
        pip3 install --break-system-packages google-genai certifi 2>/dev/null || pip3 install google-genai certifi
    elif command -v pip &>/dev/null; then
        pip install --break-system-packages google-genai certifi 2>/dev/null || pip install google-genai certifi
    else
        python3 -m pip install --break-system-packages google-genai certifi 2>/dev/null || python3 -m pip install google-genai certifi
    fi
    echo -e "${GREEN}✓ Dependencies installed.${RESET}"
fi

# ------------------------------------------------------------------------------
# 2. Check / Prompt for Google Gemini API Key
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[2/4] Checking Gemini API Key...${RESET}"

API_KEY=""

# Check command line flags (--api-key or first argument)
if [ "$1" == "--api-key" ] && [ -n "$2" ]; then
    API_KEY="$2"
elif [ -n "$1" ] && [[ "$1" != --* ]]; then
    API_KEY="$1"
fi

# Check existing config file
CONFIG_DIR="$HOME/.config/wikigpt"
CONFIG_FILE="$CONFIG_DIR/env"
if [ -z "$API_KEY" ] && [ -f "$CONFIG_FILE" ]; then
    SAVED_KEY="$(grep -E '^export GEMINI_API_KEY=' "$CONFIG_FILE" 2>/dev/null | cut -d'=' -f2 | tr -d '"' | tr -d "'")"
    if [ -n "$SAVED_KEY" ]; then
        API_KEY="$SAVED_KEY"
    fi
fi

# Check environment variable
if [ -z "$API_KEY" ] && [ -n "$GEMINI_API_KEY" ]; then
    API_KEY="$GEMINI_API_KEY"
fi

# If interactive, prompt user
if [ -t 0 ]; then
    if [ -n "$API_KEY" ]; then
        MASKED="${API_KEY:0:6}...${API_KEY: -4}"
        echo -e "${GREEN}Found existing API Key: ${MASKED}${RESET}"
        read -r -p "Do you want to use this key? [Y/n]: " keep_key
        if [[ "$keep_key" =~ ^[Nn] ]]; then
            API_KEY=""
        fi
    fi

    if [ -z "$API_KEY" ]; then
        echo -e "${YELLOW}Please enter your Google Gemini API Key.${RESET}"
        echo -e "(Get a free key here: ${BLUE}https://aistudio.google.com/app/apikey${RESET})"
        read -r -p "🔑 Gemini API Key: " user_input
        API_KEY="$(echo "$user_input" | xargs)"
    fi
fi

# Validate key presence
if [ -z "$API_KEY" ]; then
    echo -e "\n${RED}==========================================================="
    echo -e "❌ ERROR: No Gemini API Key was found or provided!"
    echo -e "===========================================================${RESET}"
    echo -e "${YELLOW}"
    echo -e "WikiGPT cannot answer questions without a Gemini API Key."
    echo -e ""
    echo -e "Follow these simple instructions to get your key:"
    echo -e "  1. Open your browser and go to:"
    echo -e "     ${BLUE}https://aistudio.google.com/app/apikey${YELLOW}"
    echo -e "  2. Sign in with your Google Account and click 'Create API key'."
    echo -e "  3. Re-run this installer:"
    echo -e "     ${BOLD}./install.sh${RESET}${YELLOW}"
    echo -e "     (or pass it directly: ${BOLD}./install.sh YOUR_KEY_HERE${RESET}${YELLOW})"
    echo -e ""
    echo -e "  Alternatively, you can manually export it in your shell profile:"
    echo -e "     ${BOLD}export GEMINI_API_KEY=\"your_key_here\"${RESET}${YELLOW}"
    echo -e "===========================================================${RESET}\n"
    exit 1
fi

# Save API key to configuration file
mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_FILE" <<EOF
# WikiGPT Environment Configuration
export GEMINI_API_KEY="$API_KEY"
EOF
chmod 600 "$CONFIG_FILE"
echo -e "${GREEN}✓ API Key safely saved to $CONFIG_FILE (chmod 600)${RESET}"

# Configure shell profiles to auto-source the key
SOURCE_LINE="[ -f \"\$HOME/.config/wikigpt/env\" ] && . \"\$HOME/.config/wikigpt/env\""
for RC in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.bash_profile"; do
    if [ -f "$RC" ]; then
        if ! grep -q "wikigpt/env" "$RC"; then
            echo "" >> "$RC"
            echo "# Added by WikiGPT Installer" >> "$RC"
            echo "$SOURCE_LINE" >> "$RC"
            echo -e "${GREEN}✓ Added environment auto-load to $RC${RESET}"
        fi
    fi
done

# ------------------------------------------------------------------------------
# 3. Install executable to PATH
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[3/4] Installing 'wikigpt' command to PATH...${RESET}"

chmod +x "$WIKIGPT_SRC"

INSTALL_DIR=""
if [ -w "/usr/local/bin" ] || [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/usr/local/bin"
else
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
fi

cp "$WIKIGPT_SRC" "$INSTALL_DIR/wikigpt"
chmod +x "$INSTALL_DIR/wikigpt"

echo -e "${GREEN}✓ Installed executable to: $INSTALL_DIR/wikigpt${RESET}"

# If installed in ~/.local/bin, make sure it's in PATH
if [ "$INSTALL_DIR" == "$HOME/.local/bin" ]; then
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        PATH_EXPORT='export PATH="$HOME/.local/bin:$PATH"'
        for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
            if [ -f "$RC" ] && ! grep -q ".local/bin" "$RC"; then
                echo "$PATH_EXPORT" >> "$RC"
                echo -e "${GREEN}✓ Added ~/.local/bin to PATH in $RC${RESET}"
            fi
        done
        export PATH="$HOME/.local/bin:$PATH"
    fi
fi

# ------------------------------------------------------------------------------
# 4. Summary & Instructions
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[4/4] Finalizing setup...${RESET}"
echo -e "${BOLD}${GREEN}"
echo "==========================================================="
echo "   🎉 WikiGPT has been successfully installed!"
echo "==========================================================="
echo -e "${RESET}"

echo -e "You can now use ${BOLD}wikigpt${RESET} directly from anywhere:"
echo ""
echo -e "  ${BOLD}1. Interactive Chat Mode (with memory & follow-ups):${RESET}"
echo -e "     ${BLUE}wikigpt${RESET}"
echo ""
echo -e "  ${BOLD}2. Quick Single-Question Mode:${RESET}"
echo -e "     ${BLUE}wikigpt \"Who discovered Penicillin?\"${RESET}"
echo ""
echo -e "  ${BOLD}3. If your current terminal doesn't recognize the command yet:${RESET}"
echo -e "     ${YELLOW}source ~/.bashrc${RESET}  (or: ${YELLOW}source ~/.zshrc${RESET})"
echo ""
echo -e "${BOLD}Enjoy exploring with WikiGPT! 📚✨${RESET}\n"