# umc (Ultimate Media Converter)

Allows for easy batch-conversion of media (music, video) using ffmpeg and python. Walks down many depths of subdirectories for files to copy/convert.

- Simple configuration files for quick parameter changes
- A thin GUI that keeps a list of recent paths
- Rough estimated encoding time
- Multithreading that scales the thread count according to encode speed, reducing I/O bottleneck

<details><summary>Why?</summary>
I was sick of writing the same `ffmpeg` batch script for converting a bunch of files over and over again. This aims to be an evolution of that in a way.
 
Doing it in Python instead of `bash` allows for configuration in a file, converting to multiple formats in one go, threaded conversions, and really easy Windows compatibility.
</details>

## Usage

### Graphical interface
Run `run-gui.py`<br>
Pick a folder and Run.<br>
Pick a preset.<br>
Edit it in a text editor if you want.<br>
Click Run again, and it'll do the work.

### CLI
Run `run.py` in the directory you want to be converted.

Unless you already configured the folder, umc will prompt you to choose an example configuration to start from.
```
Welcome to the configuration wizard.
It is assumed you want to setup UMC for this folder.
Here are presets to get you started.

<presets>
```
Feel free to review the `umc.yaml` file if you want to change the name or properties of the targets. (A target is a folder which `umc` will create then copy/convert files from the current folder into.)

Once you have a config file, run umc again. If the configuration is valid, it should start working.

### Building a binary
(FIXME: We should really use setuptools for this...)
Assuming PyInstaller is installed, run `build.py`. If the build process is successful, the binary will be placed in a new `dist` folder.

(FIXME: This folder will not be in `PATH`, so move the binary someplace in `PATH` or add the folder to `PATH`.)