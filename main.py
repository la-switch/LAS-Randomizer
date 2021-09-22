import sys
import yaml
import random

import shuffler
import spoiler
import modgenerator

# Get the path for the RomFS folder on disk. This MUST be specified, so exit if there isn't one.
if len(sys.argv) > 1:
	romPath = sys.argv.pop(1)
else:
	print('Please specify the path to a valid RomFS.')
	exit()

# Get the output directy as a command line argument. This MUST be specified, so exit if there isn't one.
if len(sys.argv) > 1:
	outdir = sys.argv.pop(1)
else:
	print('Please specify an output directory.')
	exit()

# Get the seed argument, if it exists. If the argument is the word 'random', or was not given, choose a random seed.
if len(sys.argv) > 1:
	seed = sys.argv.pop(1)
	if seed.lower() == 'random':
		random.seed()
		seed = random.getrandbits(32)
else:
	random.seed()
	seed = random.getrandbits(32)

# Get the logic argument, or default to basic.
if len(sys.argv) > 1:
	logic = sys.argv.pop(1)
else:
	logic = 'basic'

# Get other settings off the command line arguments.
allSettings = ['fast-trendy', 'free-fishing', 'free-shop', 'free-book']
settings = []

for setting in allSettings:
	if setting in sys.argv:
		settings.append(setting)


# TEMPORARY CODE HERE to make it so that everything that isn't a chest is set to vanilla
with open("logic.yml", 'r') as logicFile:
	logicDefs = yaml.safe_load(logicFile)
nonChests = list(filter( lambda l: logicDefs[l]['type'] == 'item' and logicDefs[l]['subtype'] != 'chest' , logicDefs))


# Create a placement, spoiler log, and game mod.
print(f'Shuffling item placements... (Seed: {seed} Logic: {logic})')
placements = shuffler.makeRandomizedPlacement(seed, logic, [], nonChests, settings, False)

print('Creating spoiler log...')
spoiler.generateSpoilerLog(placements, outdir, seed)

print('Generating mod files...')
modgenerator.makeMod(placements, romPath, outdir)


print('All done! Check the Github page for instructions on how to play!')