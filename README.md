# LAS-Randomizer
A randomizer for The Legend of Zelda: Link's Awakening remake. Currently still very early in development.

The early release version available now allows for shuffling all the chests in the game, and only the chests. More work will come soon.

Please note that this early in development, not everything is guaranteed to be functional, and there is a definite possibility of the logic resulting in softlocks. This will be especially true with the glitched logic. It is recommended to primarily play the basic logic and make backup saves before going into an area that you might not be able to exit (e.g. going into Angler Tunnel without the flippers or the feather and neither are there).

**NOTE**: There is a known issue with some seeds, rarely, getting stuck during generation. If this happens, just try again with a different seed. It should take in the vicinity of 10-20 seconds to generate, so much longer than that means it's probably stuck.

In order to run the randomizer, you must have the RomFS of the game extracted and on the device you're running this program from. This can be extracted through tools like [Hactool](https://github.com/SciresM/hactool). The RomFS is the component of the game package with all of the data files (i.e. non-executable files).

Join the [Discord](https://discord.com/invite/rfBSCUfzj8) to talk about the randomizer or ask any questions you have!

## How to run:

You will need to have Python 3 installed.  Version 3.9+ is recommended to be sure the program will work. You will also need to install 2 libraries through pip, pyyaml and evfl. It can be done with the following:

`pip install pyyaml`

`pip install evfl`

Now run the following on the command line from the directory with the randomizer code:

`python main.py <RomFS path> <output directory> <seed> <logic> <other settings, space separated>`

First two arguments must be specified. The rom path should be the top level RomFS folder, i.e. the one which contains `region_common` etc.
The output directory is where the files generated by the randomizer will be created. This will be created if it doesn't exist, so you can just call it `outout` or something similar. For these file paths, please ensure you provide them using forward slashes (`/`) and not backslashes (`\`). Windows uses backslashes for file paths, so make sure you change them if you're copying one.

Seed can be any string. If specified as `random` (case insensitive), or omitted, it will use a random seed based on system time.

Valid logics are `basic`, `advanced`, `glitched`, and `none`. Omitting this will default to basic logic. Note that the advanced and glitched logics are not fully complete yet. No logic is almost certainly not beatable.

Valid extra options currently are the following (more to come in future updates):
```
free-book : the magnifying lens is not required to read the book which reveals the egg path.
```

## How to play:

To play the randomizer, you will need a homebrewed Switch console.

The randomizer does not provide a second copy of the game to use, but rather makes use of the LayeredFS system for applying game mods. The simple way to explain this system is that we will provide a secondary RomFS which is external to the game's internal RomFS, and will force the game to use any corresponding external file instead of the internal one, provided an external one exists. This functionality is simple to set up.

(See also: [Switch game modding](https://nh-server.github.io/switch-guide/extras/game_modding/))

On your SD card for your homebrew setup, navigate to the `Atmosphere/contents` folder and create a new directory named `01006BB00C6F0000`. Copy and paste the `RomFS` folder from the randomizer output into this new folder. That is, the folder structure here should look like `Atmosphere/contents/01006BB00C6F0000/RomFs/...`. After this, relaunch CFW and simply start up Link's Awakening to play the randomizer!

Applying this mod will not in any way affect your save data, so don't delete anything you don't want deleted. You will need to manually clear these files out of the mod folder to go back to the original game after.
