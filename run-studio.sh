#!/bin/bash
# Launch CNC Design Studio (local or container)

set -e

usage() {
    echo "Usage: $0 [local|container]"
    echo "  local     - Run Flask app locally (requires .venv)"
    echo "  container - Run in Podman container"
    exit 1
}

MODE=${1:-local}

case $MODE in
    local)
        echo "Starting CNC Design Studio (local mode)..."
        echo "URL: http://localhost:5000"
        echo ""

        if [ ! -d ".venv" ]; then
            echo "Error: .venv not found. Run setup first."
            exit 1
        fi

        source .venv/bin/activate
        python webapp/app.py
        ;;

    container)
        echo "Starting CNC Design Studio (container mode)..."
        echo ""

        # Check if podman is installed
        if ! command -v podman &> /dev/null; then
            echo "Podman not found. Install with: brew install podman"
            echo "Then initialize: podman machine init && podman machine start"
            exit 1
        fi

        # Check if podman machine is running
        if ! podman machine list | grep -q "Currently running"; then
            echo "Starting Podman machine..."
            podman machine start
        fi

        # Build and run
        echo "Building container..."
        podman build -t cnc-studio -f Containerfile .

        echo ""
        echo "Starting container..."
        echo "URL: http://localhost:5000"
        echo ""
        echo "Press Ctrl+C to stop"
        echo ""

        podman run --rm -it \
            -p 5000:5000 \
            -v $(pwd)/parts:/app/parts \
            -v $(pwd)/lib:/app/lib \
            -v $(pwd)/exports:/app/exports \
            --name cnc-studio \
            cnc-studio
        ;;

    *)
        usage
        ;;
esac
