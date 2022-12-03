# umc
Ultimate Media Converter (name sucks; contribute your own in a Github issue!)

Allows for easy batch-conversion of media (music, video) using ffmpeg and python. Walks down many depths of subdirectories for files to copy/convert.

## Why?
I was sick of writing the same `ffmpeg` batch script for converting a bunch of files over and over again. This aims to be an evolution of that in a way.
 
Doing it in Python instead of `bash` allows for configuration in a file, converting to multiple formats in one go, threaded conversions, and really easy Windows compatibility.

## Usage
Run the program in the directory you want to be converted.

Unless you already configured the folder, umc will prompt you to choose an example configuration to start from.
```
Welcome to the configuration wizard.
It is assumed you want to setup UMC for this folder.
Here are presets to get you started.

<presets>
```
Feel free to review the `umc.yaml` file if you want to change the name or properties of the targets. (A target is a folder which `umc` will create then copy/convert files from the current folder into.)

Once you have a config file, run umc again. If the configuration is valid, it should start working.

## Contributing
Get the necessary packages from `pip`:
```
pip install -r requirements.txt
```
You can test the application without rebuilding using `run.py`.

### Building a binary
Assuming PyInstaller is installed, run `build.py`. If the build process is successful, the binary will be placed in a new `dist` folder.

(FIXME: This folder will not be in `PATH`, so move the binary someplace in `PATH` or add the folder to `PATH`.)