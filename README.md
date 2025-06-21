# Sypic

A (very) simple image viewer made in python with moderngl and pillow

I made this to have a simple image viewer that has zero UI to have a minimalist look

## ✨ Features and Controls

image scales to fit window size there is no zoom or panning functionality

arguments:

 `-n` : use nearest texture filtering (good for pixel art)

 `-m` : set max amount of cached images (default is 2 because of preloading) 

 `-bg <color>` : set hex background color e.g. #FF00FF for magenta

 `--disable-preload` : disable preloading the next image (not recommended) 

controls:

 `j` : next image
 
 `k` : previous image

## 🔧 Install to PATH (with virtual environment)

These steps will install the program somewhere local (like ~/.local/opt) and set it up so you can run it from anywhere using your terminal.
### 📁 Clone the repo and set up:

```bash 
# Create folders if they don't already exist
mkdir -p ~/.local/opt
mkdir -p ~/.local/bin

# Clone the repo
git clone https://github.com/sykotes/sypic.git ~/.local/opt/sypic

# Enter the repo
cd ~/.local/opt/sypic

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make the script executable
chmod +x sypic.sh

# Add a symlink to your local bin
ln -s ~/.local/opt/sypic/sypic.sh ~/.local/bin/sypic
```

### 📌 Notes:

If you want the repo somewhere else, replace ~/.local/opt with your preferred path.
Make sure ~/.local/bin is in your PATH. You can check by running: `echo $PATH` 
