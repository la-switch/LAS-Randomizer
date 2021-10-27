import yaml
import os

def generateSpoilerLog(placements, outputDir, seedName):
	# Open logic YAML
	with open("logic.yml", 'r') as logicFile:
		logicDefs = yaml.safe_load(logicFile)

	# Make the output directory if it doesnt exist
	if not os.path.exists(outputDir):
		os.makedirs(outputDir)

	regions = {'mabe-village': [], 'toronbo-shores': [], 'mysterious-woods': [], 'koholint-prairie': [], 'tabahl-wasteland': [], 'ukuku-prairie': [], 'sign-maze': [], 'goponga-swamp': [], 'taltal-heights': [], 'marthas-bay': [], 'kanalet-castle': [], 'pothole-field': [], 'animal-village': [], 'yarna-desert': [], 'ancient-ruins': [], 'rapids-ride': [], 'taltal-mountains-east': [], 'taltal-mountains-west': [], 'color-dungeon': [], 'tail-cave': [], 'bottle-grotto': [], 'key-cavern': [], 'angler-tunnel': [], 'catfish-maw': [], 'face-shrine': [], 'eagle-tower': [], 'turtle-rock': []}

	for key in logicDefs:
		if logicDefs[key]['type'] == 'item' or logicDefs[key]['type'] == 'follower':
			regions[logicDefs[key]['spoiler-region']].append(key)

	with open(f'{outputDir}/spoiler_{seedName}.txt', 'w') as output:
		for key in regions:
			output.write(f'{key}:\n')
			for location in regions[key]:
				output.write('  {0}: {1}\n'.format(location, placements[location]))

		output.write('settings:\n')
		for setting in placements['settings']:
			if setting != 'excluded-locations':
				output.write(f'  {setting}: {placements["settings"][setting]}\n')

		output.write('excluded-locations:\n')
		for location in placements['force-junk']:
			output.write(f'  {location}\n')