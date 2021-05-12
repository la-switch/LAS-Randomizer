import yaml
import re
import random

# Open logic YAML
with open("logic.yml", 'r') as logicFile:
	logicDefs = yaml.safe_load(logicFile)

# Open items YAML
with open("items.yml", 'r') as itemFile:
	itemDefs = yaml.safe_load(itemFile)

def addAccess(access, new):
	if new in access:
		access[new] += 1
	else:
		access[new] = 1

	return access


def removeAccess(access, toRemove):
	if toRemove in access:
		access[toRemove] -= 1
		if access[toRemove] == 0:
			access.pop(toRemove)
	return access


def hasAccess(access, key, amount=1):
	return key in access and access[key] >= amount


def checkAccess(newCheck, access, logic):
	# get the name of the check without the parameter sometimes applied to enemy checks
	noParams = re.match('[a-zA-Z0-9-]+', newCheck).group(0)

	if logicDefs[noParams]['type'] == 'enemy':
		param = re.search('\\[([a-z]+)\\]', newCheck)
		if param:
			return eval(parseCondition(logicDefs[noParams]['condition-basic'])) or eval(parseCondition(logicDefs[noParams]['condition-'+param.group(1)]))
		else:
			return eval(parseCondition(logicDefs[noParams]['condition-basic']))
	else:
		# For item and follower checks, see if you have access to the region. Otherwise, check on the conditions, if they exist
		regionAccess = hasAccess(access, logicDefs[newCheck]['region']) if (logicDefs[newCheck]['type'] == 'item' or logicDefs[newCheck]['type'] == 'follower') else True
		basic        = eval(parseCondition(logicDefs[newCheck]['condition-basic']))    if ('condition-basic' in logicDefs[newCheck]) else True
		advanced     = eval(parseCondition(logicDefs[newCheck]['condition-advanced'])) if (('condition-advanced' in logicDefs[newCheck]) and (logic == 'advanced' or logic == 'glitched')) else False
		glitched     = eval(parseCondition(logicDefs[newCheck]['condition-glitched'])) if (('condition-glitched' in logicDefs[newCheck]) and logic == 'glitched') else False
		return regionAccess and (basic or advanced or glitched)


def parseCondition(condition):
	func = condition
	func = re.sub('([a-zA-Z0-9\\-\\[\\]]+)(:(\\d+))?', lambda match: f'hasAccess(access, "{match.group(1)}", {match.group(3) or 1})', func)
	func = re.sub('\\|', 'or', func)
	func = re.sub('&', 'and', func)
	return func


def canReachLocation(toReach, placements, startingAccess, logic):
	"""Given a set of item placements, and a starting item set, verify whether the location toReach is possible from the start of the game
	
	Parameters
	----------
	toReach : str
		The name of the location to check
	placements : dict
		Full of <location : str, item : str> pairs to represent items placed in locations. Currently empty locations have the value None.
	startingAccess : dict
		A dict of <item : str, quantity : int> pairs. The starting item/access set to consider, i.e. all items not yet placed
	logic : str
		The logic to use in verifying. 'basic', 'advanced', or 'glitched'

	Returns True or False depending on whether access is eventually gained to toReach.
	"""
	access = startingAccess.copy()
	accessAdded = True

	while accessAdded:
		accessAdded = False
		for key in logicDefs:
			if key not in access:
				#print(key)
				if checkAccess(key, access, logic):
					access = addAccess(access, key)
					accessAdded = True
					# if this is the location we were looking for, we're done!
					if key == toReach:
						return True

					# if we're looking at an item or follower location, at the item it holds, if it has one
					if (logicDefs[key]['type'] == 'item' or logicDefs[key]['type'] == 'follower') and placements[key] != None:
						access = addAccess(access, placements[key])

					# if we're looking at an enemy, and we CAN kill it, then we can also kill it with access to pits or heavy objects, so add those too
					if logicDefs[key]['type'] == 'enemy':
						access = addAccess(access, key+'[pit]')
						access = addAccess(access, key+'[heavy]')
				# if we can't do the thing, but it's an enemy, we might be able to use pits or heavy throwables, so check those cases independently
				elif logicDefs[key]['type'] == 'enemy':
					if 'condition-pit' in logicDefs[key]:
						if checkAccess(key+'[pit]', access, logic):
							access = addAccess(access, key)
							accessAdded = True
					if 'condition-heavy' in logicDefs[key]:
						if checkAccess(key+'[heavy]', access, logic):
							access = addAccess(access, key)
							accessAdded = True

	# If we get stuck and can't find any more locations to add, then we're stuck and can't reach toReach
	return False




def makeRandomizedPlacement(seed, logic, forceJunk, forceVanilla):
	"""Creates and returns a a randomized placement of items, adhering to the logic

	Parameters
	----------
	seed : int
		The seed to initialize the randomness.
	logic : str
		The logic to use in verifying. 'basic', 'advanced', or 'glitched'
	forceJunk : list
		A list of strings as location names, which should be forced to hold junk items.
	forceVanilla : list
		A list of strings as location names, which should be forced to hold the same item they do in the normal game.
		forceJunk takes priority over forceVanilla
	"""

	random.seed(0)

	# Initialize the item and location lists, and the structures for tracking placements and access
	access = {}
	importantItems = []
	seashellItems = []
	goodItems = []
	junkItems = []
	dungeonItems = []
	locations = []
	placements = {}

	for key in logicDefs:
		if logicDefs[key]['type'] == 'item':
			locations.append(key)
			placements[key] = None
			access = addAccess(access, logicDefs[key]['content']) # we're going to assume the player starts with everything, then slowly loses things as they get placed into the wild

	# For each type of item in the item pool, add its quantity to the item lists
	for key in itemDefs:
		if itemDefs[key]['type'] == 'important':
			importantItems += [key] * itemDefs[key]['quantity']
		elif itemDefs[key]['type'] == 'seashell':
			seashellItems += [key] * itemDefs[key]['quantity']
		elif itemDefs[key]['type'] == 'good':
			goodItems += [key] * itemDefs[key]['quantity']
		elif itemDefs[key]['type'] == 'junk':
			junkItems += [key] * itemDefs[key]['quantity']
		else:
			dungeonItems += [key] * itemDefs[key]['quantity']

	# First put followers in now. At first, leave vanilla. TODO: add randomization
	placements |= {'moblin-cave': 'bow-wow', 'rooster-statue': 'rooster'}

	# Assign junk into the forceJunk locations
	random.shuffle(junkItems)

	for loc in forceJunk:
		# If it's not a valid location name, just ignore it
		if loc not in locations:
			continue

		# Zol traps and the master stalfos note can only exist in chests.
		# So, we want to move them to the end of the junk list until we find something we can put in a chest
		while (junkItems[0] == 'zol-trap' or junkItems[0] == 'stalfos-note') and logicDefs[loc]['subtype'] != 'chest':
			junkItems.append(junkItems.pop(0))

		# Add the first element of the junk list into loc, and store it in placements.
		# Also, remove loc from the locations list because we already dealt with it
		placements[loc] = junkItems.pop(0)
		access = removeAccess(access, placements[loc])
		locations.remove(loc)

	# Shuffle item and location lists
	random.shuffle(importantItems)
	random.shuffle(seashellItems)
	random.shuffle(goodItems)
	items = importantItems + seashellItems + goodItems + junkItems + dungeonItems

	random.shuffle(locations)

	# Assign vanilla contents to forceVanilla locations
	for loc in forceVanilla:
		# If it's not a valid location name, or already used for forceJunk, just ignore it
		if loc not in locations:
			continue

		# Place the defined vanilla content
		placements[loc] = logicDefs[loc]['content']
		items.remove(logicDefs[loc]['content'])
		access = removeAccess(access, logicDefs[loc]['content'])
		locations.remove(loc)
	
	# Next, assign dungeon items into their own dungeons
	# Some may have been placed already because of forceVanilla so we need to factor that in
	dungeons = ['color-dungeon', 'tail-cave', 'bottle-grotto', 'key-cavern', 'angler-tunnel', 'catfish-maw', 'face-shrine', 'eagle-tower', 'turtle-rock']
	for i in range(len(dungeons)):
		itemPool = list(filter((lambda s: len(s) >= 2 and s[-2:] == f'D{i}'), items))
		locationPool = list(filter((lambda s: len(s) >= 2 and s[:2] == f'D{i}'), locations))
		random.shuffle(locationPool)

		# Iterate through the dungeon items for that dungeon (inherently in order of nightmare key, small keys, stone beak, compass, map)
		while itemPool:
			item = itemPool[0]
			print(item+' -> ', end='')

			# Until we make a valid placement for this item
			validPlacement = False
			while validPlacement == False:
				# Try placing the first item in the list in the first location
				placements[locationPool[0]] = item
				access = removeAccess(access, item)

				# Check if it's reachable there
				validPlacement = canReachLocation(locationPool[0], placements, access, logic)
				if validPlacement == False:
					# If it's not, take back the item and shift that location to the end of the list
					access = addAccess(access, item)
					placements[locationPool[0]] = None
					locationPool.append(locationPool.pop(0))

			# After we successfully made a valid placement, remove the item and location from consideration
			print(locationPool[0])
			items.remove(item)
			itemPool.remove(item)
			locations.remove(locationPool[0])
			locationPool.pop(0)
			#print(placements)

	# Place the zol traps and master stalfos note. These HAVE to go in chests so we need to do them first
	toPlace = list(filter(lambda s: s == 'zol-trap' or s == 'stalfos-note', items))
	chests = list(filter(lambda s: logicDefs[s]['subtype'] == 'chest', locations))
	for item in toPlace:
		print(item+' -> ', end='')
		chest = chests.pop(0)
		placements[chest] = item
		items.remove(item)
		locations.remove(chest)
		print(chests[0])

	# Do a very similar process for all other items
	while items:
		item = items.pop(0)
		print(item+' -> ', end='')

		# Until we make a valid placement for this item
		validPlacement = False
		while validPlacement == False:
			# Try placing the first item in the list in the first location
			placements[locations[0]] = item
			access = removeAccess(access, item)

			# Check for item type restrictions, i.e. songs can't be standing items
			if (item in ['song-ballad', 'song-mambo', 'song-soul', 'bomb-capacity', 'arrow-capacity', 'powder-capacity']) and (logicDefs[locations[0]]['subtype'] in ['standing', 'hidden', 'dig', 'drop', 'boss', 'underwater', 'shop']):
				validPlacement = False
			elif (item in ['zol-trap', 'stalfos-note']) and logicDefs[locations[0]]['subtype'] != 'chest':
				validPlacement = False
			# Check if it's reachable there. We only need to do this check for important items! good and junk items are never needed in logic
			elif itemDefs[item]['type'] == 'important' or itemDefs[item]['type'] == 'seashell':
				validPlacement = canReachLocation(locations[0], placements, access, logic)
			else:
				validPlacement = True

			# If it wasn't valid, put it back and shift the first location to the end of the list
			if validPlacement == False:
				access = addAccess(access, item)
				placements[locations[0]] = None
				#print(f'shifting locations list: {len(locations)} -> ', end='')
				locations.append(locations.pop(0))
				#print(len(locations))

		# After we successfully made a valid placement, remove the item and location from consideration
		print(locations[0])
		locations.pop(0)
		#print(f'{len(items)} {len(locations)}')
	#print(access)
	#print(canReachLocation('D0-fairy-1', placements, access, 'basic'))
	return placements




#print(parseCondition('D1-8C & kill-hardhat-beetle[pit]'))

placements = makeRandomizedPlacement(0, 'basic', ['dampe-page-1-first', 'dampe-page-1-second', 'dampe-page-2', 'dampe-bottle', 'dampe-page-3'], 
	['D1-instrument', 'D2-instrument', 'D3-instrument', 'D4-instrument', 'D5-instrument', 'D6-instrument', 'D7-instrument', 'D8-instrument',
	'trendy-prize-1', 'mamasha', 'ciao-ciao', 'sale', 'kiki', 'tarin-ukuku', 'chef-bear', 'papahl', 'christine-trade', 'mr-write', 'grandma-yahoo', 'bay-fisherman', 'mermaid-martha', 'mermaid-cave',
	'kanalet-crow', 'kanalet-mad-bomber', 'kanalet-kill-room', 'kanalet-bombed-guard', 'kanalet-final-guard'])

regions = {'mabe-village': [], 'toronbo-shores': [], 'mysterious-woods': [], 'koholint-prairie': [], 'ukuku-prairie': [], 'sign-maze': [], 'goponga-swamp': [], 'taltal-heights': [], 'marthas-bay': [], 'kanalet-castle': [], 'pothole-field': [], 'animal-village': [], 'yarna-desert': [], 'ancient-ruins': [], 'rapids-ride': [], 'taltal-mountains-east': [], 'taltal-mountains-west': [], 'color-dungeon': [], 'tail-cave': [], 'bottle-grotto': [], 'key-cavern': [], 'angler-tunnel': [], 'catfish-maw': [], 'face-shrine': [], 'eagle-tower': [], 'turtle-rock': []}

for key in logicDefs:
	if logicDefs[key]['type'] == 'item' or logicDefs[key]['type'] == 'follower':
		regions[logicDefs[key]['spoiler-region']].append(key)


with open('output.txt', 'w') as output:
	for key in regions:
		output.write(f'{key}:\n')
		for location in regions[key]:
			output.write('  {0}: {1}\n'.format(location, placements[location]))