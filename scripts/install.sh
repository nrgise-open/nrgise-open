#!/bin/bash


# Check if the --dev switch is provided
if [ "$1" == "--dev" ]; then
    echo "Installing NRGISE in development mode..."
    pip install -e .[dev]
    conda install ipopt=3.14 -y --override-channels -c conda-forge
else
    echo "Installing package..."
    pip install -e .
fi

# Check the status of the installation
if [ $? -eq 0 ]; then
    echo "NRGISE installed successfully."
else
    echo "NRGISE installation failed."
fi
