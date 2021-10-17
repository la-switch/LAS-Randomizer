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

	if logic == 'none': return True

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

	# if using no logic, we don't have to check if it's reachable, we just assume it is.
	if logic == 'none':
		return True

	access = startingAccess.copy()
	accessAdded = True

	while accessAdded:
		accessAdded = False
		for key in logicDefs:
			if key not in access:
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
					if 'condition-pit' in logicDefs[key] and not hasAccess(access, key+'[pit]'):
						if checkAccess(key+'[pit]', access, logic):
							access = addAccess(access, key+'[pit]')
							accessAdded = True
					if 'condition-heavy' in logicDefs[key] and not hasAccess(access, key+'[heavy]'):
						if checkAccess(key+'[heavy]', access, logic):
							access = addAccess(access, key+'[heavy]')
							accessAdded = True

	# If we get stuck and can't find any more locations to add, then we're stuck and can't reach toReach
	return False


def verifySeashellsAttainable(placements, startingAccess, logic, goal):
	# Verify, given the starting access to items, whether it is possible to get up to [goal] seashells. This includes already placed shells (vanilla) or 
	locations = []
	access = startingAccess.copy()
	accessAdded = True

	# This check is run before random shells are placed, so any seashell come across during this runthrough
	# must have been forced vanilla. We don't want to count these directly in access.
	vanillaSeashells = 0

	while accessAdded:
		accessAdded = False
		for key in logicDefs:
			if key not in access:
				if checkAccess(key, access, logic) or logic == 'none':
					access = addAccess(access, key)
					accessAdded = True

					# if we're looking at an item or follower location, at the item it holds, if it has one
					if (logicDefs[key]['type'] == 'item' or logicDefs[key]['type'] == 'follower') and placements[key] != None:
						if placements[key] == 'seashell':
							vanillaSeashells += 1
						else:
							access = addAccess(access, placements[key])

					if logicDefs[key]['type'] == 'item' and placements[key] == None:
						locations.append(key)

					# if we're looking at an enemy, and we CAN kill it, then we can also kill it with access to pits or heavy objects, so add those too
					if logicDefs[key]['type'] == 'enemy':
						access = addAccess(access, key+'[pit]')
						access = addAccess(access, key+'[heavy]')
				# if we can't do the thing, but it's an enemy, we might be able to use pits or heavy throwables, so check those cases independently
				elif logicDefs[key]['type'] == 'enemy':
					if 'condition-pit' in logicDefs[key] and not hasAccess(access, key+'[pit]'):
						if checkAccess(key+'[pit]', access, logic):
							access = addAccess(access, key+'[pit]')
							accessAdded = True
					if 'condition-heavy' in logicDefs[key] and not hasAccess(access, key+'[heavy]'):
						if checkAccess(key+'[heavy]', access, logic):
							access = addAccess(access, key+'[heavy]')
							accessAdded = True

	#print(len(locations), numRandom, access['seashell'], goal)
	#print(access)
	return len(locations) + vanillaSeashells >= goal



def makeRandomizedPlacement(seed, logic, forceJunk, forceVanilla, settings, verbose=False):
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

	random.seed(seed)

	# Make sure logic is a valid value, default to basic
	logic = logic.lower()
	if logic not in ['basic', 'advanced', 'glitched', 'none']:
		logic = 'basic'

	# Initialize the item and location lists, and the structures for tracking placements and access
	access = {}
	importantItems = []
	seashellItems = []
	goodItems = []
	junkItems = []
	dungeonItems = []
	locations = []
	placements = {}

	vanillaSeashells = 0 # Keep track of how many seashells were forced into their vanilla locations. This is important for ensuring there is enough room to place the random ones.

	placements['settings'] = settings
	placements['force-junk'] = []
	placements['force-vanilla'] = []
	placements['indexes'] = {}

	indexesAvailable = {'seashell': list(range(50)), 'heart-piece': list(range(32)), 'heart-container': list(range(9)), 'bottle': list(range(3)), 'golden-leaf': list(range(5))}

	for key in logicDefs:
		if logicDefs[key]['type'] == 'item':
			locations.append(key)
			placements[key] = None
			access = addAccess(access, logicDefs[key]['content']) # we're going to assume the player starts with everything, then slowly loses things as they get placed into the wild

	# Add the settings into the access. This affects some logic like with fast trendy, free fishing, etc.
	settingsAccess = {setting: 1 for setting in settings}
	access.update(settingsAccess)

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

	# Randomly place bow-wow and the rooster
	"""followers = ['bow-wow', 'rooster']
	random.shuffle(followers)
	placements['moblin-cave'] = followers[0]
	placements['rooster-statue'] = followers[1]"""

	# Force the followers to be vanilla (for now)
	placements['moblin-cave'] = 'bow-wow'
	placements['rooster-statue'] = 'rooster'

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
		placedItem = junkItems.pop(0)
		placements[loc] = placedItem
		access = removeAccess(access, placements[loc])
		locations.remove(loc)

		# If the item is one that needs an index, give it the next available one
		if placedItem in indexesAvailable:
			placements['indexes'][loc] = indexesAvailable[placedItem].pop(0)

		placements['force-junk'].append(loc)

	# Shuffle item and location lists
	random.shuffle(importantItems)
	random.shuffle(seashellItems)
	random.shuffle(goodItems)
	items = importantItems + seashellItems + goodItems + junkItems + dungeonItems

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

		if logicDefs[loc]['content'] == 'seashell':
			vanillaSeashells += 1

		# If the item is one that needs an index, assign it its vanilla item index and remove that from the available indexes
		if logicDefs[loc]['content'] in indexesAvailable:
			placements['indexes'][loc] = logicDefs[loc]['index']
			indexesAvailable[logicDefs[loc]['content']].remove(logicDefs[loc]['index'])

		placements['force-vanilla'].append(loc)
	
	# Next, assign dungeon items into their own dungeons
	# Some may have been placed already because of forceVanilla so we need to factor that in
	dungeons = ['color-dungeon', 'tail-cave', 'bottle-grotto', 'key-cavern', 'angler-tunnel', 'catfish-maw', 'face-shrine', 'eagle-tower', 'turtle-rock']
	for i in range(len(dungeons)):
		itemPool = list(filter((lambda s: len(s) >= 2 and s[-2:] == f'D{i}'), items))
		locationPool = list(filter((lambda s: len(s) >= 2 and s[:2] == f'D{i}'), locations))
		random.shuffle(locationPool)

		# Keep track of where we placed items. this is necessary to undo placements if we get stuck
		placementTracker = []

		# Iterate through the dungeon items for that dungeon (inherently in order of nightmare key, small keys, stone beak, compass, map)
		while itemPool:
			item = itemPool[0]
			if verbose: print(item+' -> ', end='')
			firstLocationTried = locationPool[0]

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
					if locationPool[0] == firstLocationTried: 
						# If we tried every location and none work, undo the previous placement and try putting it somewhere else. Also rerandomize the location list to ensure things aren't placed back in the same spots
						undoLocation = placementTracker.pop(0)
						locationPool.append(undoLocation)
						locations.append(undoLocation)
						random.shuffle(locationPool)
						items.insert(0, placements[undoLocation])
						itemPool.insert(0, placements[undoLocation])
						access = addAccess(access, placements[undoLocation])
						placements[undoLocation] = None
						if verbose: print("can't place")
						break

			if validPlacement:
				# After we successfully made a valid placement, remove the item and location from consideration
				items.remove(item)
				itemPool.remove(item)
				if verbose: print(locationPool[0])
				locations.remove(locationPool[0])
				placementTracker.append(locationPool.pop(0))

	# Shuffle remaining locations
	random.shuffle(locations)

	# Place the zol traps and master stalfos note. These HAVE to go in chests so we need to do them first
	toPlace = list(filter(lambda s: s == 'zol-trap' or s == 'stalfos-note', items))
	chests = list(filter(lambda s: logicDefs[s]['subtype'] == 'chest', locations))
	for item in toPlace:
		if verbose: print(item+' -> ', end='')
		chest = chests.pop(0)
		placements[chest] = item
		items.remove(item)
		locations.remove(chest)
		if verbose: print(chests[0])

	# Next, place an item on Tarin. Since Tarin is the only check available with no items, he has to have something out of a certain subset of items
	# Only do this if Tarin has no item placed, i.e. not forced to be vanilla
	if placements['tarin'] == None:
		success = False
		while success == False:
			placements['tarin'] = items[0]
			success = canReachLocation('can-shop', placements, settingsAccess, logic) or canReachLocation('break-bush', placements, settingsAccess, logic)
			if success == False:
				items.insert(items.index('seashell'), items[0])
				items.pop(0)

		if verbose: print(items[0]+' -> tarin')
		access = removeAccess(access, items.pop(0))
		locations.remove('tarin')

	# Keep track of where we placed items. this is necessary to undo placements if we get stuck
	placementTracker = []

	# Do a very similar process for all other items
	while items:
		item = items[0]
		if verbose: print(item+' -> ', end='')
		firstLocationTried = locations[0]

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
			elif itemDefs[item]['type'] == 'important' or itemDefs[item]['type'] == 'seashell':
				# Check if it's reachable there. We only need to do this check for important items! good and junk items are never needed in logic
				validPlacement = canReachLocation(locations[0], placements, access, logic)
			else:
				validPlacement = True

			# If it wasn't valid, put it back and shift the first location to the end of the list
			if validPlacement == False:
				access = addAccess(access, item)
				placements[locations[0]] = None
				locations.append(locations.pop(0))
				if locations[0] == firstLocationTried: 
					# If we tried every location and none work, undo the previous placement and try putting it somewhere else
					undoLocation = placementTracker.pop(0)
					locations.append(undoLocation)
					random.shuffle(locations)
					items.insert(0, placements[undoLocation])
					access = addAccess(access, placements[undoLocation])
					placements[undoLocation] = None
					if verbose: print("can't place")
					break

		if validPlacement:
			# After we successfully made a valid placement, remove the item and location from consideration
			if verbose: print(locations[0])

			placedItem = items.pop(0)
			# If the item is one that needs an index, give it the next available one
			if placedItem in indexesAvailable:
				placements['indexes'][locations[0]] = indexesAvailable[placedItem].pop(0)

			placementTracker.append(locations.pop(0))

			# If we placed the last important item (so that afterward we start placing seashells), we want to ensure there's enough available locations to place a number of seashells required.
			# i.e., are there 40 locations reachable without getting the 40 and 50 rewards? If not, we haven't made a valid placement, so we have to go back and undo things until this is resolved.
			if item != 'seashell' and len(items) > 0 and items[0] == 'seashell':
				if not ((verifySeashellsAttainable(placements, settingsAccess, logic, 5)) 
				  and (verifySeashellsAttainable(placements, settingsAccess, logic, 15))
				  and (verifySeashellsAttainable(placements, settingsAccess, logic, 30))
				  and (verifySeashellsAttainable(placements, settingsAccess, logic, 40))
				  and (verifySeashellsAttainable(placements, settingsAccess, logic, 50))):
					if verbose: 
						print('no room for shells')
						#print(placements)
					undoLocation = placementTracker.pop(0)
					locations.append(undoLocation)
					random.shuffle(locations)
					items.insert(0, placements[undoLocation])
					access = addAccess(access, placements[undoLocation])
					placements[undoLocation] = None

	return placements
