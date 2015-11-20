require_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "This program requires root privileges."
        exit 1
    fi
}
