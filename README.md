# Cloud-Compiler
Cloud compiler for compiling Parallax Propeller Spin and C projects.

## Manuals
### Prerequisite

#### Python
This application is written for Python 2.7, on a unix based system (bsd, linux, Mac) although it may may work on Windows but it is not supported.
Official testing is done on a headless Debian 8.1.

Required python libraries, available for installation using easy_install or pip:

- [flask](http://flask.pocoo.org/docs/0.10/installation/)

#### Propeller C compiler
You will need to have the Propeller C compiler installed. 

If you haven't installed it already, and you install Cloud-Compiler on a headless server, you will still have to install [SimpleIDE](http://learn.parallax.com/propeller-c-set-simpleide/linux) as there currently is no installer available with just the compiler.
Follow the Linux directions described on the [Simple IDE with Propeller GCC Installation Instructions](https://d9d46cb6fc558ba1db5c3aa51f1eb3a56e713404.googledrive.com/host/0B8ruEl5BL0dfZzZfdHRiX2pYNm8/Installation_Instructions.pdf) but only up to step 3.
There is no need to install the dependencies (libqtgui4, libqtcore4 and libftdi1) or add the user to the dialout group as the server will not have to connect to a the Propeller using serial communication.
 
#### Propeller Simple libraries
Download and extract the latest [Simple libraries](http://learn.parallax.com/propeller-c-set-simpleide/update-your-learn-folder)

#### OpenSpin compiler
If you have installed the Propeller C compiler, it will contain the OpenSpin compiler.

#### Spin libraries
If you have installed the Propeller C compiler, it will contain the Spin libraries, otherwise install the *Propeller Tool* on another system and copy the directory containing the spin files from the installed files. 

### Setup
Make sure all prerequisites are fulfilled, then clone the project.

No building is required, using `python cloudcompiler.py` you can start the server. But first configure the application

### Configuration

Create a text file called **cloudcompiler.properties** in the users home directory and with the following configurations:
 
- C compiler executable: **c-compiler**. Defaults to: */opt/parallax/bin/propeller-elf-gcc*
- C library location (simple libraries): **c-libraries**. Defaults to: */opt/simple-libraries*
- Spin compiler executable: **spin-compiler**. Defaults to */opt/parallax/bin/openspin*
- Spin library location: **spin-libraries**. Defaults to */opt/parallax/spin*

For example:

```
c-libraries = /home/compiler/simple-libraries
```
