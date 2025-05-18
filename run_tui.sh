#!/bin/bash
# Text-based User Interface (TUI) for LaTeX2Video
# This script provides a simple menu-based interface for the CLI version
# that works in WSL2 environments without requiring X11.

# Default paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_CONFIG="$SCRIPT_DIR/config/config.yaml"
DEFAULT_OUTPUT="$SCRIPT_DIR/output"
LATEX_FILE=""

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to display a header
print_header() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                       ${CYAN}LaTeX2Video TUI${BLUE}                        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to display the current settings
print_settings() {
    echo -e "${YELLOW}Current Settings:${NC}"
    echo -e "  ${CYAN}LaTeX File:${NC}       ${LATEX_FILE:-Not set}"
    echo -e "  ${CYAN}Config File:${NC}      ${CONFIG_FILE:-$DEFAULT_CONFIG}"
    echo -e "  ${CYAN}Output Directory:${NC} ${OUTPUT_DIR:-$DEFAULT_OUTPUT}"
    echo ""
}

# Function to select a file
select_file() {
    local title=$1
    local file_type=$2
    local default_dir=$3
    
    print_header
    echo -e "${YELLOW}$title${NC}"
    echo -e "Please enter the path to the $file_type file, or press Enter to browse:"
    echo -e "(Current directory: $(pwd))"
    echo ""
    read -e -p "> " file_path
    
    if [ -z "$file_path" ]; then
        # Use find to list files of the specified type
        echo -e "\nSearching for $file_type files..."
        echo -e "Please select a file from the list below:"
        echo ""
        
        # Find files and display them with numbers
        files=($(find "$default_dir" -type f -name "*.$file_type" 2>/dev/null))
        
        if [ ${#files[@]} -eq 0 ]; then
            echo -e "${RED}No $file_type files found in $default_dir${NC}"
            echo -e "Press Enter to continue..."
            read
            return 1
        fi
        
        for i in "${!files[@]}"; do
            echo -e "$((i+1)). ${files[$i]}"
        done
        
        echo ""
        read -p "Enter the number of the file to select (or 0 to cancel): " file_num
        
        if [ -z "$file_num" ] || [ "$file_num" -eq 0 ]; then
            return 1
        fi
        
        if [ "$file_num" -gt 0 ] && [ "$file_num" -le "${#files[@]}" ]; then
            file_path="${files[$((file_num-1))]}"
        else
            echo -e "${RED}Invalid selection.${NC}"
            echo -e "Press Enter to continue..."
            read
            return 1
        fi
    fi
    
    # Check if the file exists
    if [ ! -f "$file_path" ]; then
        echo -e "${RED}File not found: $file_path${NC}"
        echo -e "Press Enter to continue..."
        read
        return 1
    fi
    
    echo -e "${GREEN}Selected file: $file_path${NC}"
    echo -e "Press Enter to continue..."
    read
    
    echo "$file_path"
    return 0
}

# Function to select a directory
select_directory() {
    local title=$1
    local default_dir=$2
    
    print_header
    echo -e "${YELLOW}$title${NC}"
    echo -e "Please enter the path to the directory, or press Enter to use the default:"
    echo -e "(Default: $default_dir)"
    echo ""
    read -e -p "> " dir_path
    
    if [ -z "$dir_path" ]; then
        dir_path="$default_dir"
    fi
    
    # Create the directory if it doesn't exist
    mkdir -p "$dir_path"
    
    echo -e "${GREEN}Selected directory: $dir_path${NC}"
    echo -e "Press Enter to continue..."
    read
    
    echo "$dir_path"
    return 0
}

# Function to run a CLI command
run_cli_command() {
    local args=$1
    local wait_message=$2
    local success_message=$3
    
    if [ -z "$LATEX_FILE" ]; then
        print_header
        echo -e "${RED}Error: No LaTeX file selected.${NC}"
        echo -e "Press Enter to continue..."
        read
        return 1
    fi
    
    print_header
    echo -e "${YELLOW}$wait_message${NC}"
    echo ""
    
    # Build the command
    cmd="python3 run_cli.py \"$LATEX_FILE\""
    
    # Add config file if specified
    if [ ! -z "$CONFIG_FILE" ]; then
        cmd="$cmd -c \"$CONFIG_FILE\""
    fi
    
    # Add any additional arguments
    if [ ! -z "$args" ]; then
        cmd="$cmd $args"
    fi
    
    # Run the command
    echo -e "${CYAN}Running command: $cmd${NC}"
    echo ""
    eval $cmd
    
    # Check the result
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}$success_message${NC}"
    else
        echo ""
        echo -e "${RED}Command failed with return code $?${NC}"
    fi
    
    echo -e "Press Enter to continue..."
    read
    
    return 0
}

# Main menu
main_menu() {
    while true; do
        print_header
        print_settings
        
        echo -e "${YELLOW}Main Menu:${NC}"
        echo -e "  ${CYAN}1.${NC} Select LaTeX File"
        echo -e "  ${CYAN}2.${NC} Select Config File"
        echo -e "  ${CYAN}3.${NC} Select Output Directory"
        echo -e "  ${CYAN}4.${NC} Generate Scripts"
        echo -e "  ${CYAN}5.${NC} Generate Images"
        echo -e "  ${CYAN}6.${NC} Generate Audio"
        echo -e "  ${CYAN}7.${NC} Assemble Video"
        echo -e "  ${CYAN}8.${NC} Generate All"
        echo -e "  ${CYAN}0.${NC} Exit"
        echo ""
        read -p "Enter your choice: " choice
        
        case $choice in
            1)
                result=$(select_file "Select LaTeX File" "tex" "$SCRIPT_DIR")
                if [ $? -eq 0 ]; then
                    LATEX_FILE="$result"
                fi
                ;;
            2)
                result=$(select_file "Select Config File" "yaml" "$SCRIPT_DIR/config")
                if [ $? -eq 0 ]; then
                    CONFIG_FILE="$result"
                fi
                ;;
            3)
                result=$(select_directory "Select Output Directory" "$DEFAULT_OUTPUT")
                if [ $? -eq 0 ]; then
                    OUTPUT_DIR="$result"
                fi
                ;;
            4)
                run_cli_command "--save-scripts" "Generating narration scripts..." "Narration scripts generated successfully."
                ;;
            5)
                run_cli_command "--images-only" "Generating slide images..." "Slide images generated successfully."
                ;;
            6)
                run_cli_command "--audio-only" "Generating audio files..." "Audio files generated successfully."
                ;;
            7)
                run_cli_command "--assemble-only" "Assembling video..." "Video assembled successfully."
                ;;
            8)
                run_cli_command "" "Generating everything..." "Video generation complete."
                ;;
            0)
                print_header
                echo -e "${GREEN}Thank you for using LaTeX2Video TUI!${NC}"
                echo ""
                exit 0
                ;;
            *)
                print_header
                echo -e "${RED}Invalid choice. Please try again.${NC}"
                echo -e "Press Enter to continue..."
                read
                ;;
        esac
    done
}

# Start the main menu
main_menu
