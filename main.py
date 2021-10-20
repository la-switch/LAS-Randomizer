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
vanillaLocations = list(filter( lambda l: logicDefs[l]['type'] == 'item' and logicDefs[l]['subtype'] not in ['chest', 'boss', 'drop'] , logicDefs))
vanillaLocations.remove('tarin')
vanillaLocations.remove('washed-up')
vanillaLocations.remove('marin')
vanillaLocations.remove('christine-grateful')
vanillaLocations.remove('invisible-zora')
vanillaLocations.remove('ghost-reward')
vanillaLocations.remove('walrus')
vanillaLocations.remove('D0-fairy-1')
vanillaLocations.remove('D0-fairy-2')
vanillaLocations.remove('goriya-trader')
vanillaLocations.remove('manbo')
vanillaLocations.remove('mamu')
vanillaLocations.remove('rapids-race-45')
vanillaLocations.remove('rapids-race-35')
vanillaLocations.remove('rapids-race-30')
vanillaLocations.remove('fishing-any')
vanillaLocations.remove('fishing-cheep-cheep')
vanillaLocations.remove('fishing-ol-baron')
vanillaLocations.remove('fishing-50')
vanillaLocations.remove('fishing-100')
vanillaLocations.remove('fishing-150')
vanillaLocations.remove('fishing-loose')
vanillaLocations.remove('5-seashell-reward')
vanillaLocations.remove('15-seashell-reward')
vanillaLocations.remove('30-seashell-reward')
vanillaLocations.remove('40-seashell-reward')
vanillaLocations.remove('50-seashell-reward')
vanillaLocations.remove('mad-batter-bay')
vanillaLocations.remove('mad-batter-woods')
vanillaLocations.remove('mad-batter-taltal')
vanillaLocations.remove('dampe-page-1')
vanillaLocations.remove('dampe-page-2')
vanillaLocations.remove('dampe-final')
vanillaLocations.remove('dampe-heart-challenge')
vanillaLocations.remove('dampe-bottle-challenge')
vanillaLocations.remove('trendy-prize-final')
vanillaLocations.remove('woods-loose')
vanillaLocations.remove('taltal-rooster-cave')
vanillaLocations.remove('dream-shrine-left')

vanillaLocations.append('kanalet-kill-room')
vanillaLocations.append('D4-sunken-item')

# Create a placement, spoiler log, and game mod.
print(f'Shuffling item placements... (Seed: {seed} Logic: {logic})')
placements = shuffler.makeRandomizedPlacement(seed, logic, [], vanillaLocations, settings, False)

print('Creating spoiler log...')
spoiler.generateSpoilerLog(placements, outdir, seed)

print('Generating mod files...')
modgenerator.makeMod(placements, romPath, outdir)

print('All done! Check the Github page for instructions on how to play!')