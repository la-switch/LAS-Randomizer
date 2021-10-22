import yaml
import os
import re
import copy

import leb
import eventtools
import oeadtools


swordFoundFlag     = 'unused0357'
shieldFoundFlag    = 'unused0358'
braceletFoundFlag  = 'unused0359'
redTunicFoundFlag  = 'unused0360'
blueTunicFoundFlag = 'unused0361'
goriyaFlag         = 'unused0432'
mamuFlag           = 'unused0433'
manboFlag          = 'unused0434'

roosterCaveFlag    = 'unused0707'
dreamShrineFlag    = 'unused0708'
woodsLooseFlag     = 'unused0709'

# Load the Items YAML. This is necessary to translate our naming conventions for the logic into the internal item names.
with open("items.yml", 'r') as itemsFile:
    itemDefs = yaml.safe_load(itemsFile)



def makeMod(placements, romPath, outdir):
    makeGeneralLEBChanges(placements, romPath, outdir)
    makeGeneralEventChanges(placements, romPath, outdir)
    makeGeneralDatasheetChanges(placements, romPath, outdir)

    if 'free-book' in placements['settings']:
        setFreeBook(romPath, outdir)

    makeChestContentFixes(placements, romPath, outdir)

    makeEventContentChanges(placements, romPath, outdir)

    makeSmallKeyChanges(placements, romPath, outdir)


# Patch LEB files of rooms with chests to update their contents
def makeChestContentFixes(placements, romPath, outdir):
	# Start by setting up the paths for the RomFS
	if not os.path.exists(f'{outdir}/Romfs/region_common/level'):
		os.makedirs(f'{outdir}/Romfs/region_common/level')

	for room in chestRooms:
		dirname = re.match('(.+)_\\d\\d[A-P]', chestRooms[room]).group(1)
		if not os.path.exists(f'{outdir}/Romfs/region_common/level/{dirname}'):
			os.makedirs(f'{outdir}/Romfs/region_common/level/{dirname}')

		with open(f'{romPath}/region_common/level/{dirname}/{chestRooms[room]}.leb', 'rb') as roomfile:
			roomData = leb.Room(roomfile.read())

		item = bytes(itemDefs[placements[room]]['item-key'], 'utf-8')
		itemIndex = -1
		if room in placements['indexes']:
			itemIndex = placements['indexes'][room]

		for i in range(5 if room == 'taltal-5-chest-puzzle' else 1): # use this to handle one special case where we need to write the same data to 5 chests in the same room
			if itemIndex > -1:
				roomData.setChestContent(item, i, itemIndex)
			else:
				roomData.setChestContent(item, i)

		with open(f'{outdir}/Romfs/region_common/level/{dirname}/{chestRooms[room]}.leb', 'wb') as outfile:
			outfile.write(roomData.repack())

		# Two special cases in D7 have duplicate rooms, once for pre-collapse and once for post-collapse. So we need to make sure we write the same data to both rooms.
		if room == 'D7-grim-creeper':
			with open(f'{romPath}/region_common/level/Lv07EagleTower/Lv07EagleTower_06H.leb', 'rb') as roomfile:
				roomData = leb.Room(roomfile.read())

			item = bytes(itemDefs[placements[room]]['item-key'], 'utf-8')

			if placements[room] == 'seashell':
				roomData.setChestContent(item, 0, itemIndex)
			else:
				roomData.setChestContent(item)

			with open(f'{outdir}/Romfs/region_common/level/Lv07EagleTower/Lv07EagleTower_06H.leb', 'wb') as outfile:
				outfile.write(roomData.repack())

		if room == 'D7-3f-horseheads':
			with open(f'{romPath}/region_common/level/Lv07EagleTower/Lv07EagleTower_05G.leb', 'rb') as roomfile:
				roomData = leb.Room(roomfile.read())

			item = bytes(itemDefs[placements[room]]['item-key'], 'utf-8')

			if placements[room] == 'seashell':
				roomData.setChestContent(item, 0, itemIndex)
			else:
				roomData.setChestContent(item)

			with open(f'{outdir}/Romfs/region_common/level/Lv07EagleTower/Lv07EagleTower_05G.leb', 'wb') as outfile:
				outfile.write(roomData.repack())


# Patch SmallKey event and LEB files for rooms with small key drops to change them into other items.
def makeSmallKeyChanges(placements, romPath, outdir):
    # Start by setting up the paths for the RomFS
    if not os.path.exists(f'{outdir}/Romfs/region_common/level'):
        os.makedirs(f'{outdir}/Romfs/region_common/level')

    # Open up the SmallKey event to be ready to edit
    flow = eventtools.readFlow(f'{romPath}/region_common/event/SmallKey.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    for room in smallKeyRooms:
        dirname = re.match('(.+)_\\d\\d[A-P]', smallKeyRooms[room]).group(1)
        if not os.path.exists(f'{outdir}/Romfs/region_common/level/{dirname}'):
            os.makedirs(f'{outdir}/Romfs/region_common/level/{dirname}')

        with open(f'{romPath}/region_common/level/{dirname}/{smallKeyRooms[room]}.leb', 'rb') as roomfile:
            roomData = leb.Room(roomfile.read())

        item = placements[room]
        itemIndex = placements['indexes'][room] if room in placements['indexes'] else -1

        # Don't change anything if the item placed here is actually a small key. Just leave it as the vanilla ItemSmallKey actor.
        if item[:3] == 'key':
            roomData.setSmallKeyParams(itemDefs[item]['model-path'], itemDefs[item]['model-name'], 'take')
        else:
            roomData.setSmallKeyParams(itemDefs[item]['model-path'], itemDefs[item]['model-name'], smallKeyRooms[room])

            eventtools.addEntryPoint(flow.flowchart, smallKeyRooms[room])
            
            itemEvent = insertItemGetEvent(flow.flowchart, itemDefs[item]['item-key'], itemIndex, None, None)

            eventtools.createActionChain(flow.flowchart, smallKeyRooms[room], [
                ('SmallKey', 'Deactivate', {}),
                ('SmallKey', 'SetActorSwitch', {'value': True, 'switchIndex': 1}),
                ('SmallKey', 'Destroy', {})
                ], itemEvent)


        with open(f'{outdir}/Romfs/region_common/level/{dirname}/{smallKeyRooms[room]}.leb', 'wb') as outfile:
            outfile.write(roomData.repack())

        if room == 'D4-sunken-item': # special case. need to write the same data in 06A
            with open(f'{romPath}/region_common/level/Lv04AnglersTunnel/Lv04AnglersTunnel_06A.leb', 'rb') as roomfile:
                roomData = leb.Room(roomfile.read())

            # Don't change anything if the item placed here is actually a small key. Just leave it as the vanilla ItemSmallKey actor.
            if item[:3] == 'key':
                roomData.setSmallKeyParams(itemDefs[item]['model-path'], itemDefs[item]['model-name'], 'take')
            else:
                roomData.setSmallKeyParams(itemDefs[item]['model-path'], itemDefs[item]['model-name'], smallKeyRooms[room])

            with open(f'{outdir}/Romfs/region_common/level/Lv04AnglersTunnel/Lv04AnglersTunnel_06A.leb', 'wb') as outfile:
                outfile.write(roomData.repack())


    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/SmallKey.bfevfl', flow)


# Patch event flow files to change the items given by NPCs and other events
def makeEventContentChanges(placements, romPath, outdir):
    # Run through for every location that needs an event changed.
    # Note that many of these require some extra fixes which will be handled here too.
    tarinChanges(placements, romPath, outdir)
    sinkingSwordChanges(placements, romPath, outdir)
    walrusChanges(placements, romPath, outdir)
    christineChanges(placements, romPath, outdir)
    invisibleZoraChanges(placements, romPath, outdir)
    marinChanges(placements, romPath, outdir)
    ghostRewardChanges(placements, romPath, outdir)
    clothesFairyChanges(placements, romPath, outdir)
    goriyaChanges(placements, romPath, outdir)
    manboChanges(placements, romPath, outdir)
    mamuChanges(placements, romPath, outdir)
    rapidsChanges(placements, romPath, outdir)
    fishingChanges(placements, romPath, outdir)
    trendyChanges(placements, romPath, outdir)
    seashellMansionChanges(placements, romPath, outdir)
    madBatterChanges(placements, romPath, outdir)
    dampeChanges(placements, romPath, outdir)
    moldormChanges(placements, romPath, outdir)
    genieChanges(placements, romPath, outdir)
    slimeEyeChanges(placements, romPath, outdir)
    anglerChanges(placements, romPath, outdir)
    slimeEelChanges(placements, romPath, outdir)
    facadeChanges(placements, romPath, outdir)
    eagleChanges(placements, romPath, outdir)
    hotheadChanges(placements, romPath, outdir)
    lanmolaChanges(placements, romPath, outdir)
    armosKnightChanges(placements, romPath, outdir)
    masterStalfosChanges(placements, romPath, outdir)
    

def tarinChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Tarin.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['tarin'] if 'tarin' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['tarin']]['item-key'], itemIndex, 'Event52', 'Event31')

    event0 = eventtools.findEvent(flow.flowchart, 'Event0')
    event78 = eventtools.findEvent(flow.flowchart, 'Event78')
    event0.data.actor = event78.data.actor
    event0.data.actor_query = event78.data.actor_query
    event0.data.params = event78.data.params
    
    """eventtools.createActionChain(flow.flowchart, 'Event36', [
        #('Inventory', 'AddItemByKey', {'itemKey': 'MagnifyingLens', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'SwordLv1', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'Shield', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'PegasusBoots', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'PowerBraceletLv2', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'Song_Soul', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'Ocarina', 'count': 1, 'index': -1, 'autoEquip': True}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'RocsFeather', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'HookShot', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'Boomerang', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'Flippers', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'TailKey', 'count': 1, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'Bomb', 'count': 30, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'MagicPowder', 'count': 10, 'index': -1, 'autoEquip': False}),
        ('Inventory', 'AddItemByKey', {'itemKey': 'Rupee300', 'count': 1, 'index': -1, 'autoEquip': False})
        ], 'Event52')"""

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Tarin.bfevfl', flow)

def sinkingSwordChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/SinkingSword.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    # Beach
    item = placements['washed-up']
    itemIndex = placements['indexes']['washed-up'] if 'washed-up' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[item]['item-key'], itemIndex, 'Event5', 'Event8')

    fork = eventtools.findEvent(flow.flowchart, 'Event0')
    fork.data.forks.pop(0)
    eventtools.findEvent(flow.flowchart, 'Event1').data.params.data['itemType'] = -1

    if not os.path.exists(f'{outdir}/Romfs/region_common/level/Field'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/Field')

    with open(f'{romPath}/region_common/level/Field/Field_16C.leb', 'rb') as file:
        room = leb.Room(file.read())

    room.actors[4].parameters[0] = bytes(itemDefs[item]['model-path'], 'utf-8')
    room.actors[4].parameters[1] = bytes(itemDefs[item]['model-name'], 'utf-8')
    room.actors[4].parameters[2] = bytes('examine', 'utf-8')
    room.actors[4].parameters[3] = bytes('SwordGet', 'utf-8')

    with open(f'{outdir}/Romfs/region_common/level/Field/Field_16C.leb', 'wb') as file:
        file.write(room.repack())

    # Rooster Cave (bird key)
    eventtools.addEntryPoint(flow.flowchart, 'TalTal')

    item = placements['taltal-rooster-cave']
    itemIndex = placements['indexes']['taltal-rooster-cave'] if 'taltal-rooster-cave' in placements['indexes'] else -1
    birdKeyItemGet = insertItemGetEvent(flow.flowchart, itemDefs[item]['item-key'], itemIndex, None, None)

    eventtools.createActionChain(flow.flowchart, 'TalTal', [
        ('SinkingSword', 'Destroy', {}),
        ('EventFlags', 'SetFlag', {'symbol': roosterCaveFlag, 'value': True})
        ], birdKeyItemGet)

    if not os.path.exists(f'{outdir}/Romfs/region_common/level/EagleKeyCave'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/EagleKeyCave')

    with open(f'{romPath}/region_common/level/EagleKeyCave/EagleKeyCave_01A.leb', 'rb') as file:
        room = leb.Room(file.read())

    room.actors[0].type = 0x194
    room.actors[0].parameters[0] = bytes(itemDefs[item]['model-path'], 'utf-8')
    room.actors[0].parameters[1] = bytes(itemDefs[item]['model-name'], 'utf-8')
    room.actors[0].parameters[2] = bytes('TalTal', 'utf-8')
    room.actors[0].parameters[3] = bytes(roosterCaveFlag, 'utf-8')

    with open(f'{outdir}/Romfs/region_common/level/EagleKeyCave/EagleKeyCave_01A.leb', 'wb') as file:
        file.write(room.repack())

    # Dream Shrine (ocarina)
    eventtools.addEntryPoint(flow.flowchart, 'DreamShrine')

    item = placements['dream-shrine-left']
    itemIndex = placements['indexes']['dream-shrine-left'] if 'dream-shrine-left' in placements['indexes'] else -1
    dreamShrineItemGet = insertItemGetEvent(flow.flowchart, itemDefs[item]['item-key'], itemIndex, None, None)

    eventtools.createActionChain(flow.flowchart, 'DreamShrine', [
        ('SinkingSword', 'Destroy', {}),
        ('EventFlags', 'SetFlag', {'symbol': dreamShrineFlag, 'value': True})
        ], dreamShrineItemGet)

    if not os.path.exists(f'{outdir}/Romfs/region_common/level/DreamShrine'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/DreamShrine')

    with open(f'{romPath}/region_common/level/DreamShrine/DreamShrine_01A.leb', 'rb') as file:
        room = leb.Room(file.read())

    room.actors[5].type = 0x194
    room.actors[5].parameters[0] = bytes(itemDefs[item]['model-path'], 'utf-8')
    room.actors[5].parameters[1] = bytes(itemDefs[item]['model-name'], 'utf-8')
    room.actors[5].parameters[2] = bytes('DreamShrine', 'utf-8')
    room.actors[5].parameters[3] = bytes(dreamShrineFlag, 'utf-8')

    with open(f'{outdir}/Romfs/region_common/level/DreamShrine/DreamShrine_01A.leb', 'wb') as file:
        file.write(room.repack())

    # Woods (mushroom)
    eventtools.addEntryPoint(flow.flowchart, 'Woods')

    item = placements['woods-loose']
    itemIndex = placements['indexes']['woods-loose'] if 'woods-loose' in placements['indexes'] else -1
    woodsItemGet = insertItemGetEvent(flow.flowchart, itemDefs[item]['item-key'], itemIndex, None, None)

    eventtools.createActionChain(flow.flowchart, 'Woods', [
        ('SinkingSword', 'Destroy', {}),
        ('EventFlags', 'SetFlag', {'symbol': woodsLooseFlag, 'value': True})
        ], woodsItemGet)

    if not os.path.exists(f'{outdir}/Romfs/region_common/level/Field'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/Field')

    with open(f'{romPath}/region_common/level/Field/Field_06A.leb', 'rb') as file:
        room = leb.Room(file.read())

    room.actors[3].type = 0x194
    room.actors[3].parameters[0] = bytes(itemDefs[item]['model-path'], 'utf-8')
    room.actors[3].parameters[1] = bytes(itemDefs[item]['model-name'], 'utf-8')
    room.actors[3].parameters[2] = bytes('Woods', 'utf-8')
    room.actors[3].parameters[3] = bytes(woodsLooseFlag, 'utf-8')

    with open(f'{outdir}/Romfs/region_common/level/Field/Field_06A.leb', 'wb') as file:
        file.write(room.repack())

    # Done!
    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/SinkingSword.bfevfl', flow)

def walrusChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Walrus.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['walrus'] if 'walrus' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['walrus']]['item-key'], itemIndex, 'Event53', 'Event110')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Walrus.bfevfl', flow)

def christineChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Christine.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['christine-grateful'] if 'christine-grateful' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['christine-grateful']]['item-key'], itemIndex, 'Event44', 'Event36')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Christine.bfevfl', flow)

def invisibleZoraChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/SecretZora.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['invisible-zora'] if 'invisible-zora' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['invisible-zora']]['item-key'], itemIndex, 'Event23', 'Event27')

    eventtools.insertEventAfter(flow.flowchart, 'Event32', 'Event23')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/SecretZora.bfevfl', flow)

def marinChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Marin.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['marin'] if 'marin' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['marin']]['item-key'], itemIndex, 'Event246', 'Event666')

    fork = eventtools.findEvent(flow.flowchart, 'Event249')
    fork.data.forks.pop(0)
    eventtools.insertEventAfter(flow.flowchart, 'Event27', 'Event249')
    event20 = eventtools.findEvent(flow.flowchart, 'Event20')
    event160 = eventtools.findEvent(flow.flowchart, 'Event160')
    event676 = eventtools.findEvent(flow.flowchart, 'Event676')
    event160.data.actor = event20.data.actor
    event676.data.actor = event20.data.actor
    event160.data.actor_query = event20.data.actor_query
    event676.data.actor_query = event20.data.actor_query
    event160.data.params.data['symbol'] = 'MarinsongGet'
    event676.data.params.data['symbol'] = 'MarinsongGet'

    # Make Marin not do beach_talk under any circumstance
    eventtools.setSwitchEventCase(flow.flowchart, 'Event21', 0, 'Event674')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Marin.bfevfl', flow)

def ghostRewardChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Owl.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    new = eventtools.createActionEvent(flow.flowchart, 'Owl', 'Destroy', {})

    itemIndex = placements['indexes']['ghost-reward'] if 'ghost-reward' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['ghost-reward']]['item-key'], itemIndex, 'Event34', new)

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Owl.bfevfl', flow)

def clothesFairyChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/FairyQueen.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D0-fairy-2'] if 'D0-fairy-2' in placements['indexes'] else -1
    item2 = insertItemGetEvent(flow.flowchart, itemDefs[placements['D0-fairy-2']]['item-key'], itemIndex, 'Event0', 'Event180')

    itemIndex = placements['indexes']['D0-fairy-1'] if 'D0-fairy-1' in placements['indexes'] else -1
    item1 = insertItemGetEvent(flow.flowchart, itemDefs[placements['D0-fairy-1']]['item-key'], itemIndex, 'Event0', item2)

    eventtools.insertEventAfter(flow.flowchart, 'Event128', 'Event58')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/FairyQueen.bfevfl', flow)

def goriyaChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Goriya.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    flagEvent = eventtools.createActionEvent(flow.flowchart, 'EventFlags', 'SetFlag', {'symbol': goriyaFlag, 'value': True}, 'Event4')

    itemIndex = placements['indexes']['goriya-trader'] if 'goriya-trader' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['goriya-trader']]['item-key'], itemIndex, 'Event87', flagEvent)

    flagCheck = eventtools.createSwitchEvent(flow.flowchart, 'EventFlags', 'CheckFlag', {'symbol': goriyaFlag}, {0: 'Event7', 1: 'Event15'})
    eventtools.insertEventAfter(flow.flowchart, 'Event24', flagCheck)

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Goriya.bfevfl', flow)

def manboChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/ManboTamegoro.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    flagEvent = eventtools.createActionEvent(flow.flowchart, 'EventFlags', 'SetFlag', {'symbol': manboFlag, 'value': True}, 'Event13')

    itemIndex = placements['indexes']['manbo'] if 'manbo' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['manbo']]['item-key'], itemIndex, 'Event31', flagEvent)

    flagCheck = eventtools.createSwitchEvent(flow.flowchart, 'EventFlags', 'CheckFlag', {'symbol': manboFlag}, {0: 'Event37', 1: 'Event35'})
    eventtools.insertEventAfter(flow.flowchart, 'Event9', flagCheck)

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/ManboTamegoro.bfevfl', flow)

def mamuChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Mamu.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    flagEvent = eventtools.createActionEvent(flow.flowchart, 'EventFlags', 'SetFlag', {'symbol': mamuFlag, 'value': True}, 'Event40')

    itemIndex = placements['indexes']['mamu'] if 'mamu' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['mamu']]['item-key'], itemIndex, 'Event85', flagEvent)

    flagCheck = eventtools.createSwitchEvent(flow.flowchart, 'EventFlags', 'CheckFlag', {'symbol': mamuFlag}, {0: 'Event14', 1: 'Event98'})
    eventtools.insertEventAfter(flow.flowchart, 'Event10', flagCheck)

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Mamu.bfevfl', flow)

def rapidsChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/RaftShopMan.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['rapids-race-45'] if 'rapids-race-45' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['rapids-race-45']]['item-key'], itemIndex, 'Event42', 'Event88')

    itemIndex = placements['indexes']['rapids-race-35'] if 'rapids-race-35' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['rapids-race-35']]['item-key'], itemIndex, 'Event40', 'Event86')

    itemIndex = placements['indexes']['rapids-race-30'] if 'rapids-race-30' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['rapids-race-30']]['item-key'], itemIndex, 'Event38', 'Event85')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/RaftShopMan.bfevfl', flow)

def fishingChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Fisherman.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    changeDefs = [
        ('fishing-any', 'Event113', 'Event212'),
        ('fishing-cheep-cheep', 'Event3', 'Event10'),
        ('fishing-ol-baron', 'Event133', 'Event140'),
        ('fishing-50', 'Event182', 'Event240'),
        ('fishing-100', 'Event191', 'Event247'),
        ('fishing-150', 'Event193', 'Event255'),
        ('fishing-loose', 'Event264', 'Event265')
    ]

    for defs in changeDefs:
        itemIndex = placements['indexes'][defs[0]] if defs[0] in placements['indexes'] else -1
        insertItemGetEvent(flow.flowchart, itemDefs[placements[defs[0]]]['item-key'], itemIndex, defs[1], defs[2])

    eventtools.insertEventAfter(flow.flowchart, 'Event20', 'Event3')
    eventtools.insertEventAfter(flow.flowchart, 'Event18', 'Event133')
    eventtools.insertEventAfter(flow.flowchart, 'Event24', 'Event191')
    eventtools.insertEventAfter(flow.flowchart, 'FishingGetBottle', 'Event264')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Fisherman.bfevfl', flow)

def trendyChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/GameShopOwner.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['trendy-prize-final'] if 'trendy-prize-final' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['trendy-prize-final']]['item-key'], itemIndex, 'Event112', 'Event239')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/GameShopOwner.bfevfl', flow)

def seashellMansionChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/ShellMansionMaster.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['5-seashell-reward'] if '5-seashell-reward' in placements['indexes'] else -1
    eventtools.findEvent(flow.flowchart, 'Event36').data.params.data = {'pointIndex': 0, 'itemKey': itemDefs[placements['5-seashell-reward']]['item-key'], 'itemIndex': itemIndex, 'flag': 'GetSeashell10'}

    itemIndex = placements['indexes']['15-seashell-reward'] if '15-seashell-reward' in placements['indexes'] else -1
    eventtools.findEvent(flow.flowchart, 'Event10').data.params.data = {'pointIndex': 0, 'itemKey': itemDefs[placements['15-seashell-reward']]['item-key'], 'itemIndex': itemIndex, 'flag': 'GetSeashell20'}

    itemIndex = placements['indexes']['30-seashell-reward'] if '30-seashell-reward' in placements['indexes'] else -1
    eventtools.findEvent(flow.flowchart, 'Event11').data.params.data = {'pointIndex': 0, 'itemKey': itemDefs[placements['30-seashell-reward']]['item-key'], 'itemIndex': itemIndex, 'flag': 'GetSeashell30'}

    itemIndex = placements['indexes']['50-seashell-reward'] if '50-seashell-reward' in placements['indexes'] else -1
    eventtools.findEvent(flow.flowchart, 'Event13').data.params.data = {'pointIndex': 0, 'itemKey': itemDefs[placements['50-seashell-reward']]['item-key'], 'itemIndex': itemIndex, 'flag': 'GetSeashell50'}

    # 40 shells, doesn't use a present box
    eventtools.findEvent(flow.flowchart, 'Event65').data.forks.pop(0)

    eventtools.insertEventAfter(flow.flowchart, 'Event64', 'Event65')

    # Remove the thing to show Link's sword because it will show L1 sword if he has none. 
    swordCheck1 = eventtools.createSwitchEvent(flow.flowchart, 'EventFlags', 'CheckFlag', {'symbol': swordFoundFlag}, {0: 'Event65', 1: 'Event64'})
    eventtools.insertEventAfter(flow.flowchart, 'Event80', swordCheck1)

    # However, leave it the 2nd time if he's going to get one here.
    if placements['40-seashell-reward'] != 'sword':
        swordCheck2 = eventtools.createSwitchEvent(flow.flowchart, 'EventFlags', 'CheckFlag', {'symbol': swordFoundFlag}, {0: 'Event48', 1: 'Event47'})
        eventtools.insertEventAfter(flow.flowchart, 'Event54', swordCheck2)

    itemIndex = placements['indexes']['40-seashell-reward'] if '40-seashell-reward' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['40-seashell-reward']]['item-key'], itemIndex, 'Event91', 'Event79')

    # Special case, if there is a sword here, then actually give them item before the end of the animation so it looks like the vanilla cutscene :)
    if placements['40-seashell-reward'] == 'sword':
        earlyGiveSword1 = eventtools.createActionEvent(flow.flowchart, 'Inventory', 'AddItemByKey', {'itemKey': 'SwordLv1', 'count': 1, 'index': -1, 'autoEquip': False}, 'Event19')
        earlyGiveSword2 = eventtools.createActionEvent(flow.flowchart, 'Inventory', 'AddItemByKey', {'itemKey': 'SwordLv2', 'count': 1, 'index': -1, 'autoEquip': False}, 'Event19')
        swordCheck3 = eventtools.createSwitchEvent(flow.flowchart, 'EventFlags', 'CheckFlag', {'symbol': swordFoundFlag}, {0: earlyGiveSword1, 1: earlyGiveSword2})
        eventtools.insertEventAfter(flow.flowchart, 'Event74', swordCheck3)
    else:
        eventtools.insertEventAfter(flow.flowchart, 'Event74', 'Event19')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/ShellMansionMaster.bfevfl', flow)

def madBatterChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/MadBatter.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    # Combine Talk and End entry points into one flow, cutting out the normal choose your upgrade dialogue.
    eventtools.insertEventAfter(flow.flowchart, 'Event19', 'Event13')

    ## Mad Batter A (bay)
    eventtools.addEntryPoint(flow.flowchart, 'BatterA')
    subflowA = eventtools.createSubFlowEvent(flow.flowchart, '', 'talk2', {})

    eventtools.insertEventAfter(flow.flowchart, 'BatterA', subflowA)

    itemIndex = placements['indexes']['mad-batter-bay'] if 'mad-batter-bay' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['mad-batter-bay']]['item-key'], itemIndex, subflowA, 'Event23')

    ## Mad Batter B (woods)
    eventtools.addEntryPoint(flow.flowchart, 'BatterB')
    subflowB = eventtools.createSubFlowEvent(flow.flowchart, '', 'talk2', {})

    eventtools.insertEventAfter(flow.flowchart, 'BatterB', subflowB)

    itemIndex = placements['indexes']['mad-batter-woods'] if 'mad-batter-woods' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['mad-batter-woods']]['item-key'], itemIndex, subflowB, 'Event23')

    ## Mad Batter C (mountain)
    eventtools.addEntryPoint(flow.flowchart, 'BatterC')
    subflowC = eventtools.createSubFlowEvent(flow.flowchart, '', 'talk2', {})

    eventtools.insertEventAfter(flow.flowchart, 'BatterC', subflowC)

    itemIndex = placements['indexes']['mad-batter-taltal'] if 'mad-batter-taltal' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['mad-batter-taltal']]['item-key'], itemIndex, subflowC, 'Event23')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/MadBatter.bfevfl', flow)

def dampeChanges(placements, romPath, outdir):
    sheet = oeadtools.readSheet(f'{romPath}/region_common/datasheets/MapPieceClearReward.gsheet')

    # Page 1 reward
    itemIndex = placements['indexes']['dampe-page-1'] if 'dampe-page-1' in placements['indexes'] else -1
    sheet['values'][3]['mRewardItem'] = itemDefs[placements['dampe-page-1']]['item-key']
    sheet['values'][3]['mRewardItemEventEntry'] = itemDefs[placements['dampe-page-1']]['item-key']
    sheet['values'][3]['mRewardItemIndex'] = itemIndex

    # Page 2 reward
    itemIndex = placements['indexes']['dampe-page-2'] if 'dampe-page-2' in placements['indexes'] else -1
    sheet['values'][7]['mRewardItem'] = itemDefs[placements['dampe-page-2']]['item-key']
    sheet['values'][7]['mRewardItemEventEntry'] = itemDefs[placements['dampe-page-2']]['item-key']
    sheet['values'][7]['mRewardItemIndex'] = itemIndex

    # FInal reward
    itemIndex = placements['indexes']['dampe-final'] if 'dampe-final' in placements['indexes'] else -1
    sheet['values'][12]['mRewardItem'] = itemDefs[placements['dampe-final']]['item-key']
    sheet['values'][12]['mRewardItemEventEntry'] = itemDefs[placements['dampe-final']]['item-key']
    sheet['values'][12]['mRewardItemIndex'] = itemIndex

    oeadtools.writeSheet(f'{outdir}/Romfs/region_common/datasheets/MapPieceClearReward.gsheet', sheet)

    #######

    sheet = oeadtools.readSheet(f'{romPath}/region_common/datasheets/MapPieceTheme.gsheet')

    # 1-4 reward
    itemIndex = placements['indexes']['dampe-heart-challenge'] if 'dampe-heart-challenge' in placements['indexes'] else -1
    sheet['values'][3]['mRewardItem'] = itemDefs[placements['dampe-heart-challenge']]['item-key']
    sheet['values'][3]['mRewardItemEventEntry'] = itemDefs[placements['dampe-heart-challenge']]['item-key']
    sheet['values'][3]['mRewardItemIndex'] = itemIndex

    # 3-2 reward
    itemIndex = placements['indexes']['dampe-bottle-challenge'] if 'dampe-bottle-challenge' in placements['indexes'] else -1
    sheet['values'][9]['mRewardItem'] = itemDefs[placements['dampe-bottle-challenge']]['item-key']
    sheet['values'][9]['mRewardItemEventEntry'] = itemDefs[placements['dampe-bottle-challenge']]['item-key']
    sheet['values'][9]['mRewardItemIndex'] = itemIndex

    oeadtools.writeSheet(f'{outdir}/Romfs/region_common/datasheets/MapPieceTheme.gsheet', sheet)

def moldormChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/DeguTail.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D1-moldorm'] if 'D1-moldorm' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['D1-moldorm']]['item-key'], itemIndex, 'Event8', 'Event45')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/DeguTail.bfevfl', flow)

def genieChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/PotDemonKing.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D2-genie'] if 'D2-genie' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['D2-genie']]['item-key'], itemIndex, 'Event29', 'Event56')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/PotDemonKing.bfevfl', flow)

def slimeEyeChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/DeguZol.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D3-slime-eye'] if 'D3-slime-eye' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['D3-slime-eye']]['item-key'], itemIndex, 'Event29', 'Event43')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/DeguZol.bfevfl', flow)

def anglerChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Angler.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D4-angler'] if 'D4-angler' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['D4-angler']]['item-key'], itemIndex, 'Event25', 'Event50')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Angler.bfevfl', flow)

def slimeEelChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Hooker.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D5-slime-eel'] if 'D5-slime-eel' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['D5-slime-eel']]['item-key'], itemIndex, 'Event28', 'Event13')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Hooker.bfevfl', flow)

def facadeChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/MatFace.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D6-facade'] if 'D6-facade' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['D6-facade']]['item-key'], itemIndex, 'Event8', 'Event35')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/MatFace.bfevfl', flow)

def eagleChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Albatoss.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D7-eagle'] if 'D7-eagle' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['D7-eagle']]['item-key'], itemIndex, 'Event3', 'Event51')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Albatoss.bfevfl', flow)

def hotheadChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/DeguFlame.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D8-hothead'] if 'D8-hothead' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['D8-hothead']]['item-key'], itemIndex, 'Event13', 'Event15')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/DeguFlame.bfevfl', flow)

def lanmolaChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/Lanmola.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['lanmola'] if 'lanmola' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['lanmola']]['item-key'], itemIndex, 'Event34', 'Event9')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Lanmola.bfevfl', flow)

def armosKnightChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/DeguArmos.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['armos-knight'] if 'armos-knight' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['armos-knight']]['item-key'], itemIndex, 'Event2', 'Event8')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/DeguArmos.bfevfl', flow)

def masterStalfosChanges(placements, romPath, outdir):
    flow = eventtools.readFlow(f'{romPath}/region_common/event/MasterStalfon.bfevfl')
    addNeededActors(flow.flowchart, romPath)

    itemIndex = placements['indexes']['D5-master-stalfos'] if 'D5-master-stalfos' in placements['indexes'] else -1
    insertItemGetEvent(flow.flowchart, itemDefs[placements['D5-master-stalfos']]['item-key'], itemIndex, 'Event37', 'Event194')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/MasterStalfon.bfevfl', flow)


# Fix some LEB files in ways that are always done, regardless of placements.
def makeGeneralLEBChanges(placements, romPath, outdir):
    ### MarinTarin house: weird hacky thing to make it not detain you on leaving the house.
    if not os.path.exists(f'{outdir}/Romfs/region_common/level/MarinTarinHouse'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/MarinTarinHouse')

    with open(f'{romPath}/region_common/level/MarinTarinHouse/MarinTarinHouse_01A.leb', 'rb') as file:
        room = leb.Room(file.read())

    room.actors.append(room.actors.pop(3))

    room.actors.insert(3, copy.deepcopy(room.actors[6]))
    room.actors[3].X += 0xB000000
    room.actors[3].Y += 0xB000000

    with open(f'{outdir}/Romfs/region_common/level/MarinTarinHouse/MarinTarinHouse_01A.leb', 'wb') as file:
        file.write(room.repack())

    ### Entrance to Mysterious Forest: Set the owl to 0 instead of 1, prevents the cutscene from triggering in some circumstances.
    # For all other owls, setting the flags is sufficient but this one sucks.
    if not os.path.exists(f'{outdir}/Romfs/region_common/level/Field'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/Field')

    with open(f'{romPath}/region_common/level/Field/Field_09A.leb', 'rb') as file:
        room = leb.Room(file.read())

    room.actors[1].parameters[0] = 0

    with open(f'{outdir}/Romfs/region_common/level/Field/Field_09A.leb', 'wb') as file:
        file.write(room.repack())

    ### Mad Batters: Give the batters a 3rd parameter for the event entry point to run
    # A: Bay
    if not os.path.exists(f'{outdir}/Romfs/region_common/level/MadBattersWell01'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/MadBattersWell01')

    with open(f'{romPath}/region_common/level/MadBattersWell01/MadBattersWell01_01A.leb', 'rb') as roomfile:
        roomData = leb.Room(roomfile.read())

    roomData.actors[2].parameters[2] = b'BatterA'

    with open(f'{outdir}/Romfs/region_common/level/MadBattersWell01/MadBattersWell01_01A.leb', 'wb') as outfile:
        outfile.write(roomData.repack())

    # B: Woods
    if not os.path.exists(f'{outdir}/Romfs/region_common/level/MadBattersWell02'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/MadBattersWell02')

    with open(f'{romPath}/region_common/level/MadBattersWell02/MadBattersWell02_01A.leb', 'rb') as roomfile:
        roomData = leb.Room(roomfile.read())

    roomData.actors[6].parameters[2] = b'BatterB'

    with open(f'{outdir}/Romfs/region_common/level/MadBattersWell02/MadBattersWell02_01A.leb', 'wb') as outfile:
        outfile.write(roomData.repack())

    # C: Mountain
    if not os.path.exists(f'{outdir}/Romfs/region_common/level/MadBattersWell03'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/MadBattersWell03')

    with open(f'{romPath}/region_common/level/MadBattersWell03/MadBattersWell03_01A.leb', 'rb') as roomfile:
        roomData = leb.Room(roomfile.read())

    roomData.actors[0].parameters[2] = b'BatterC'

    with open(f'{outdir}/Romfs/region_common/level/MadBattersWell03/MadBattersWell03_01A.leb', 'wb') as outfile:
        outfile.write(roomData.repack())

    ### Lanmola Cave: Remove the AnglerKey actor
    if not os.path.exists(f'{outdir}/Romfs/region_common/level/LanmolaCave'):
        os.makedirs(f'{outdir}/Romfs/region_common/level/LanmolaCave')

    with open(f'{romPath}/region_common/level/LanmolaCave/LanmolaCave_02A.leb', 'rb') as roomfile:
        roomData = leb.Room(roomfile.read())

    roomData.actors.pop(5) # remove angler key

    with open(f'{outdir}/Romfs/region_common/level/LanmolaCave/LanmolaCave_02A.leb', 'wb') as outfile:
        outfile.write(roomData.repack())


# Make changes to some events that should be in every seed, e.g. setting flags for having watched cutscenes
def makeGeneralEventChanges(placements, romPath, outdir):
    if not os.path.exists(f'{outdir}/Romfs/region_common/event'):
        os.makedirs(f'{outdir}/Romfs/region_common/event')

    #################################################################################################################################
    ### PlayerStart event: Sets a bunch of flags for cutscenes being watched/triggered to prevent them from ever happening.
    ### First check if ShieldGet flag was set, to only do this after getting the item from Tarin
    playerStart = eventtools.readFlow(f'{romPath}/region_common/event/PlayerStart.bfevfl')
    eventFlagsActor = eventtools.findActor(playerStart.flowchart, 'EventFlags') # Store this actor for later to add it to other event flows.

    playerStartFlagsFirstEvent = eventtools.createActionEvent(playerStart.flowchart, 'EventFlags', 'SetFlag', {'symbol': 'FirstClear', 'value': True})
    playerStartShieldGetCheckEvent = eventtools.createSwitchEvent(playerStart.flowchart, 'EventFlags', 'CheckFlag', {'symbol': 'ShieldGet'}, {0: None, 1: playerStartFlagsFirstEvent})

    eventtools.insertEventAfter(playerStart.flowchart, 'Event558', playerStartShieldGetCheckEvent)

    eventtools.createActionChain(playerStart.flowchart, playerStartFlagsFirstEvent, [
        ('EventFlags', 'SetFlag', {'symbol': 'SecondClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'ThirdClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'FourthClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'FifthClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'SixthClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'SeventhClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'NinthClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'TenthClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'EleventhClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'TwelveClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'ThirteenClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'FourteenClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'FiveteenClear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'WalrusAwaked', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'MarinRescueClear', 'value': True})
        ])

    # Remove the part that kills the rooster after D7 in Level7DungeonIn_FlyingCucco
    eventtools.insertEventAfter(playerStart.flowchart, 'Level7DungeonIn_FlyingCucco', 'Event476')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/PlayerStart.bfevfl', playerStart)

    #################################################################################################################################
    ### TreasureBox event: Adds in events to make certain items be progressive.
    treasureBox = eventtools.readFlow(f'{romPath}/region_common/event/TreasureBox.bfevfl')

    # Add the EventFlags actor and the AddItem action to the Inventory actor.
    treasureBox.flowchart.actors.append(eventFlagsActor)
    eventtools.addActorAction(eventtools.findActor(treasureBox.flowchart, 'Inventory'), 'AddItem')
    inventoryActor = eventtools.findActor(treasureBox.flowchart, 'Inventory') # Store this actor to add to another flow.
    flowControlActor = eventtools.findActor(treasureBox.flowchart, 'FlowControl')

    swordFlagCheckEvent = eventtools.createProgressiveItemSwitch(treasureBox.flowchart, 'SwordLv1', 'SwordLv2', swordFoundFlag)
    swordContentCheckEvent = eventtools.createSwitchEvent(treasureBox.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'SwordLv1'}, {0: swordFlagCheckEvent, 1: 'Event33'})
    
    shieldFlagCheckEvent = eventtools.createProgressiveItemSwitch(treasureBox.flowchart, 'Shield', 'MirrorShield', shieldFoundFlag)
    shieldContentCheckEvent = eventtools.createSwitchEvent(treasureBox.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'Shield'}, {0: shieldFlagCheckEvent, 1: swordContentCheckEvent})

    braceletFlagCheckEvent = eventtools.createProgressiveItemSwitch(treasureBox.flowchart, 'PowerBraceletLv1', 'PowerBraceletLv2', braceletFoundFlag)
    braceletContentCheckEvent = eventtools.createSwitchEvent(treasureBox.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'PowerBraceletLv1'}, {0: braceletFlagCheckEvent, 1: shieldContentCheckEvent})

    powderCapacityGetEvent = insertItemGetEvent(treasureBox.flowchart, 'MagicPowder_MaxUp', -1, None, None)
    powderCapacityCheckEvent = eventtools.createSwitchEvent(treasureBox.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'MagicPowder_MaxUp'}, {0: powderCapacityGetEvent, 1: braceletContentCheckEvent})

    bombCapacityGetEvent = insertItemGetEvent(treasureBox.flowchart, 'Bomb_MaxUp', -1, None, None)
    bombCapacityCheckEvent = eventtools.createSwitchEvent(treasureBox.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'Bomb_MaxUp'}, {0: bombCapacityGetEvent, 1: powderCapacityCheckEvent})

    arrowCapacityGetEvent = insertItemGetEvent(treasureBox.flowchart, 'Arrow_MaxUp', -1, None, None)
    arrowCapacityCheckEvent = eventtools.createSwitchEvent(treasureBox.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'Arrow_MaxUp'}, {0: arrowCapacityGetEvent, 1: bombCapacityCheckEvent})

    eventtools.insertEventAfter(treasureBox.flowchart, 'Event32', arrowCapacityCheckEvent)

    # Sets the events to give you the item before the item get sequence, mainly for red/blue tunic. Can be changed back when those get their own event chains
    eventtools.setSwitchEventCase(treasureBox.flowchart, 'Event33', 1, 'Event5')
    eventtools.setSwitchEventCase(treasureBox.flowchart, 'Event39', 0, 'Event5')
    eventtools.insertEventAfter(treasureBox.flowchart, 'Event5', 'Event0')
    eventtools.insertEventAfter(treasureBox.flowchart, 'Event0', None)

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/TreasureBox.bfevfl', treasureBox)

    #################################################################################################################################
    ### ShellMansionPresent event: Similar to TreasureBox, must make some items progressive.
    shellPresent = eventtools.readFlow(f'{romPath}/region_common/event/ShellMansionPresent.bfevfl')

    # Add the EventFlags actor and the AddItem action to the Inventory actor.
    shellPresent.flowchart.actors.append(eventFlagsActor)
    eventtools.addActorAction(eventtools.findActor(shellPresent.flowchart, 'Inventory'), 'AddItem')
    shellPresent.flowchart.actors.append(flowControlActor)

    swordFlagCheckEvent = eventtools.createProgressiveItemSwitch(shellPresent.flowchart, 'SwordLv1', 'SwordLv2', swordFoundFlag, None, 'Event0')
    swordContentCheckEvent = eventtools.createSwitchEvent(shellPresent.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'SwordLv1'}, {0: swordFlagCheckEvent, 1: 'Event3'})
    
    shieldFlagCheckEvent = eventtools.createProgressiveItemSwitch(shellPresent.flowchart, 'Shield', 'MirrorShield', shieldFoundFlag, None, 'Event0')
    shieldContentCheckEvent = eventtools.createSwitchEvent(shellPresent.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'Shield'}, {0: shieldFlagCheckEvent, 1: swordContentCheckEvent})

    braceletFlagCheckEvent = eventtools.createProgressiveItemSwitch(shellPresent.flowchart, 'PowerBraceletLv1', 'PowerBraceletLv2', braceletFoundFlag, None, 'Event0')
    braceletContentCheckEvent = eventtools.createSwitchEvent(shellPresent.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'PowerBraceletLv1'}, {0: braceletFlagCheckEvent, 1: shieldContentCheckEvent})

    powderCapacityGetEvent = insertItemGetEvent(shellPresent.flowchart, 'MagicPowder_MaxUp', -1, None, 'Event0')
    powderCapacityCheckEvent = eventtools.createSwitchEvent(shellPresent.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'MagicPowder_MaxUp'}, {0: powderCapacityGetEvent, 1: braceletContentCheckEvent})

    bombCapacityGetEvent = insertItemGetEvent(shellPresent.flowchart, 'Bomb_MaxUp', -1, None, 'Event0')
    bombCapacityCheckEvent = eventtools.createSwitchEvent(shellPresent.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'Bomb_MaxUp'}, {0: bombCapacityGetEvent, 1: powderCapacityCheckEvent})

    arrowCapacityGetEvent = insertItemGetEvent(shellPresent.flowchart, 'Arrow_MaxUp', -1, None, 'Event0')
    arrowCapacityCheckEvent = eventtools.createSwitchEvent(shellPresent.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'Arrow_MaxUp'}, {0: arrowCapacityGetEvent, 1: bombCapacityCheckEvent})

    eventtools.insertEventAfter(shellPresent.flowchart, 'Event3', 'Event4')
    eventtools.insertEventAfter(shellPresent.flowchart, 'Event4', 'Event14')
    eventtools.insertEventAfter(shellPresent.flowchart, 'Event14', 'Event0')
    eventtools.insertEventAfter(shellPresent.flowchart, 'Event25', arrowCapacityCheckEvent)

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/ShellMansionPresent.bfevfl', shellPresent)

    #################################################################################################################################
    ### MusicalInstrument event: Set ghost clear flags if you got the Surf Harp.
    musicalInstrument = eventtools.readFlow(f'{romPath}/region_common/event/MusicalInstrument.bfevfl')

    musicalInstrument.flowchart.actors.append(eventFlagsActor)
    eventtools.addActorQuery(eventtools.findActor(musicalInstrument.flowchart, 'Inventory'), 'HasItem')

    ghostFlagsSetEvent = eventtools.createActionEvent(musicalInstrument.flowchart, 'EventFlags', 'SetFlag', {'symbol': 'GhostClear1', 'value': True})

    eventtools.insertEventAfter(musicalInstrument.flowchart, 'Event52', eventtools.createSwitchEvent(musicalInstrument.flowchart, 'Inventory', 'HasItem', {'itemType': 48, 'count': 1}, {0: 'Event0', 1: ghostFlagsSetEvent}))

    eventtools.createActionChain(musicalInstrument.flowchart, ghostFlagsSetEvent, [
        ('EventFlags', 'SetFlag', {'symbol': 'Ghost2_Clear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'Ghost3_Clear', 'value': True}),
        ('EventFlags', 'SetFlag', {'symbol': 'Ghost4_Clear', 'value': True})
        ], 'Event0')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/MusicalInstrument.bfevfl', musicalInstrument)

    #################################################################################################################################
    ### Item: Add and fix some entry points for the ItemGetSequence for capcity upgrades and tunics.
    item = eventtools.readFlow(f'{romPath}/region_common/event/Item.bfevfl')

    """eventtools.addEntryPoint(item.flowchart, 'MagicPowder_MaxUp')
    eventtools.createActionChain(item.flowchart, 'MagicPowder_MaxUp', [
        ('Dialog', 'Show', {'message': 'Scenario:Lv1GetShield'})
        ])"""

    eventtools.findEntryPoint(item.flowchart, 'RedClothes').name = 'ClothesRed'
    eventtools.findEntryPoint(item.flowchart, 'BlueClothes').name = 'ClothesBlue'

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Item.bfevfl', item)

    #################################################################################################################################
    ### MadamMeowMeow: Change her behaviour to always take back BowWow if you have him, and not do anything based on having the Horn
    madam = eventtools.readFlow(f'{romPath}/region_common/event/MadamMeowMeow.bfevfl')

    # Removes BowWowClear flag being set
    eventtools.insertEventAfter(madam.flowchart, 'Event69', 'Event18')

    # Rearranging her dialogue conditions
    eventtools.insertEventAfter(madam.flowchart, 'Event22', 'Event5')
    eventtools.setSwitchEventCase(madam.flowchart, 'Event5', 0, 'Event0')
    eventtools.setSwitchEventCase(madam.flowchart, 'Event5', 1, 'Event52')
    eventtools.setSwitchEventCase(madam.flowchart, 'Event0', 0, 'Event40')
    eventtools.setSwitchEventCase(madam.flowchart, 'Event0', 1, 'Event21')
    eventtools.setSwitchEventCase(madam.flowchart, 'Event21', 0, 'Event80')
    eventtools.findEvent(madam.flowchart, 'Event21').data.params.data['symbol'] = 'BowWowJoin'

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/MadamMeowMeow.bfevfl', madam)


# Make changes to some datasheets that are general in nature and not tied to specific item placements.
def makeGeneralDatasheetChanges(placements, romPath, outdir):
    if not os.path.exists(f'{outdir}/Romfs/region_common/datasheets'):
        os.makedirs(f'{outdir}/Romfs/region_common/datasheets')

    #################################################################################################################################
    ### Npc datasheet: Change MadBatter to use actor parameter $2 as its event entry point.
    ### Also change ItemSmallKey and ObjSinkingSword to use custom models/entry points.
    ### Change ItemClothesGreen to have the small key model, which we'll kinda hack in the Items datasheet so small keys are visible 
    ### in the GenericItemGetSequence.
    ### Make Papahl appear in the mountains after trading for the pineapple instead of the getting the Bell
    npcSheet = oeadtools.readSheet(f'{romPath}/region_common/datasheets/Npc.gsheet')

    for i in range(len(npcSheet['values'])):
        if npcSheet['values'][i]['symbol'] == 'NpcMadBatter':
            batterIndex = i
        if npcSheet['values'][i]['symbol'] == 'ItemSmallKey':
            smallKeyIndex = i
        if npcSheet['values'][i]['symbol'] == 'ItemClothesGreen':
            npcSheet['values'][i]['graphics']['path'] = 'ItemSmallKey.bfres'
            npcSheet['values'][i]['graphics']['model'] = 'SmallKey'
        if npcSheet['values'][i]['symbol'] == 'NpcPapahl':
            npcSheet['values'][i]['layoutConditions'][1] = {'category': 1, 'parameter': 'PineappleGet', 'layoutID': 2}
        if npcSheet['values'][i]['symbol'] == 'ObjClothBag':
            npcSheet['values'][i]['layoutConditions'][1] = {'category': 1, 'parameter': 'PineappleGet', 'layoutID': 0}
        if npcSheet['values'][i]['symbol'] == 'ObjSinkingSword':
            swordIndex = i
        if npcSheet['values'][i]['symbol'] == 'ObjRoosterBones':
            npcSheet['values'][i]['layoutConditions'].pop(0)
        if npcSheet['values'][i]['symbol'] == 'NpcBowWow':
            npcSheet['values'][i]['layoutConditions'][2] = {'category': 3, 'parameter': 'BowWow', 'layoutID': -1}
        if npcSheet['values'][i]['symbol'] == 'NpcMadamMeowMeow':
            npcSheet['values'][i]['layoutConditions'][2] = {'category': 1, 'parameter': 'BowWowJoin', 'layoutID': 3}
            npcSheet['values'][i]['layoutConditions'].pop(1)

    npcSheet['values'][batterIndex]['eventTriggers'][0]['entryPoint'] = '$2'


    npcSheet['values'][smallKeyIndex]['graphics']['path'] = '$1'
    npcSheet['values'][smallKeyIndex]['graphics']['model'] = '$2'
    npcSheet['values'][smallKeyIndex]['eventTriggers'][2]['entryPoint'] = '$3'

    npcSheet['values'][swordIndex]['graphics']['path'] = '$0'
    npcSheet['values'][swordIndex]['graphics']['model'] = '$1'
    npcSheet['values'][swordIndex]['eventTriggers'][0]['entryPoint'] = '$2'
    npcSheet['values'][swordIndex]['layoutConditions'][0]['parameter'] = '$3'


    oeadtools.writeSheet(f'{outdir}/Romfs/region_common/datasheets/Npc.gsheet', npcSheet)

    #################################################################################################################################
    ### ItemDrop datasheet: remove HeartContainer drops 0-7, HookShot drop, AnglerKey and FaceKey drops.
    itemDropSheet = oeadtools.readSheet(f'{romPath}/region_common/datasheets/ItemDrop.gsheet')

    for i in range(len(itemDropSheet['values'])):
        if itemDropSheet['values'][i]['mKey'] == 'HeartContainer0':
            firstHeartIndex = i
        elif itemDropSheet['values'][i]['mKey'] == 'AnglerKey':
            itemDropSheet['values'][i]['mLotTable'][0]['mType'] = ''
        elif itemDropSheet['values'][i]['mKey'] == 'FaceKey':
            itemDropSheet['values'][i]['mLotTable'][0]['mType'] = ''
        elif itemDropSheet['values'][i]['mKey'] == 'HookShot':
            itemDropSheet['values'][i]['mLotTable'][0]['mType'] = ''

    for i in range(8):
        itemDropSheet['values'][firstHeartIndex+i]['mLotTable'][0]['mType'] = ''

    oeadtools.writeSheet(f'{outdir}/Romfs/region_common/datasheets/ItemDrop.gsheet', itemDropSheet)

    #################################################################################################################################
    ### Items datasheet: Set actor IDs for the capacity upgrades so they show something when you get them.
    itemsSheet = oeadtools.readSheet(f'{romPath}/region_common/datasheets/Items.gsheet')

    for item in itemsSheet['values']:
        if item['symbol'] == 'MagicPowder_MaxUp':
            item['actorID'] = 124
        if item['symbol'] == 'Bomb_MaxUp':
            item['actorID'] = 117
        if item['symbol'] == 'Arrow_MaxUp':
            item['actorID'] = 180
        if item['symbol'] == 'SmallKey':
            item['npcKey'] = 'ItemClothesGreen'

    oeadtools.writeSheet(f'{outdir}/Romfs/region_common/datasheets/Items.gsheet', itemsSheet)

    #################################################################################################################################
    ### Conditions datasheet: Change conditions on Marin being in the village, so the getting the pineapple won't send her to the beach.
    conditionsSheet = oeadtools.readSheet(f'{romPath}/region_common/datasheets/Conditions.gsheet')

    for condition in conditionsSheet['values']:
        if condition['symbol'] == 'MarinVillageStay':
            condition['conditions'].pop(1)

    oeadtools.writeSheet(f'{outdir}/Romfs/region_common/datasheets/Conditions.gsheet', conditionsSheet)



# Ensure that the flowchart has the AddItemByKey and GenericItemGetSequenceByKey actions, and the EventFlags actor
# with the SetFlag and CheckFlag action/query.
def addNeededActors(flowchart, romPath):
    try:
        eventtools.findActor(flowchart, 'Inventory')
    except ValueError:
        inventoryActor = eventtools.findActor(eventtools.readFlow(f'{romPath}/region_common/event/Tarin.bfevfl').flowchart, 'Inventory')
        flowchart.actors.append(inventoryActor)

    try:
        eventtools.findActor(flowchart, 'Inventory').find_action('AddItemByKey')
    except ValueError:
        eventtools.addActorAction(eventtools.findActor(flowchart, 'Inventory'), 'AddItemByKey')

    try:
        eventtools.findActor(flowchart, 'Link').find_action('GenericItemGetSequenceByKey')
    except ValueError:
        eventtools.addActorAction(eventtools.findActor(flowchart, 'Link'), 'GenericItemGetSequenceByKey')

    try:
        eventtools.findActor(flowchart, 'EventFlags')
    except ValueError:
        eventFlagsActor = eventtools.findActor(eventtools.readFlow(f'{romPath}/region_common/event/PlayerStart.bfevfl').flowchart, 'EventFlags')
        flowchart.actors.append(eventFlagsActor)

    try:
        eventtools.findActor(flowchart, 'EventFlags').find_action('SetFlag')
    except ValueError:
        eventtools.addActorAction(eventtools.findActor(flowchart, 'EventFlags'), 'SetFlag')

    try:
        eventtools.findActor(flowchart, 'EventFlags').find_query('CheckFlag')
    except ValueError:
        eventtools.addActorQuery(eventtools.findActor(flowchart, 'EventFlags'), 'CheckFlag')


# Inserts an AddItemByKey and a GenericItemGetSequenceByKey, or a progressive item switch (depending on the item).
# It goes after 'before' and before 'after'. Return the name of the first event in the sequence.
def insertItemGetEvent(flowchart, item, index, before, after=None):
    if item == 'PowerBraceletLv1':
        return eventtools.createProgressiveItemSwitch(flowchart, 'PowerBraceletLv1', 'PowerBraceletLv2', braceletFoundFlag, before, after)

    if item == 'SwordLv1':
        return eventtools.createProgressiveItemSwitch(flowchart, 'SwordLv1', 'SwordLv2', swordFoundFlag, before, after)

    if item == 'Shield':
        return eventtools.createProgressiveItemSwitch(flowchart, 'Shield', 'MirrorShield', shieldFoundFlag, before, after)

    if item == 'MagicPowder_MaxUp':
        return eventtools.createActionChain(flowchart, before, [
            ('Inventory', 'AddItemByKey', {'itemKey': item, 'count': 1, 'index': index, 'autoEquip': False}),
            ('Inventory', 'AddItemByKey', {'itemKey': 'MagicPowder', 'count': 40, 'index': -1, 'autoEquip': False}),
            ('Link', 'GenericItemGetSequenceByKey', {'itemKey': item, 'keepCarry': False, 'messageEntry': ''})
            ], after)

    if item == 'Bomb_MaxUp':
        return eventtools.createActionChain(flowchart, before, [
            ('Inventory', 'AddItemByKey', {'itemKey': item, 'count': 1, 'index': index, 'autoEquip': False}),
            ('Inventory', 'AddItemByKey', {'itemKey': 'Bomb', 'count': 60, 'index': -1, 'autoEquip': False}),
            ('Link', 'GenericItemGetSequenceByKey', {'itemKey': item, 'keepCarry': False, 'messageEntry': ''})
            ], after)

    if item == 'Arrow_MaxUp':
        return eventtools.createActionChain(flowchart, before, [
            ('Inventory', 'AddItemByKey', {'itemKey': item, 'count': 1, 'index': index, 'autoEquip': False}),
            ('Inventory', 'AddItemByKey', {'itemKey': 'Arrow', 'count': 60, 'index': -1, 'autoEquip': False}),
            ('Link', 'GenericItemGetSequenceByKey', {'itemKey': item, 'keepCarry': False, 'messageEntry': ''})
            ], after)

    return eventtools.createActionChain(flowchart, before, [
        ('Inventory', 'AddItemByKey', {'itemKey': item, 'count': 1, 'index': index, 'autoEquip': False}),
        ('Link', 'GenericItemGetSequenceByKey', {'itemKey': item, 'keepCarry': False, 'messageEntry': ''})
        ], after)


# Set the event for the book of dark secrets to reveal the egg path without having the magnifying lens
def setFreeBook(romPath, outdir):
    book = eventtools.readFlow(f'{romPath}/region_common/event/Book.bfevfl')

    eventtools.insertEventAfter(book.flowchart, 'Event18', 'Event73')

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Book.bfevfl', book)


chestRooms = {
 'beach-chest': 'Field_15F',
 'taltal-entrance-chest': 'Tamaranch04_02D',
 'taltal-east-left-chest': 'Field_02I',
 'dream-shrine-right': 'DreamShrine_01B',
 'armos-cave': 'ArmosShrineCave_01A',
 'goponga-cave-left': 'GopongaCave_01A',
 'goponga-cave-right': 'GopongaCave_01B',
 'ukuku-cave-west-chest': 'UkukuCave01_01A',
 'ukuku-cave-east-chest': 'UkukuCave02_02A',
 'kanalet-south-cave': 'KanaletCastleSouthCave_01A',
 'rapids-middle-island': 'Field_06N',
 'rapids-south-island': 'Field_07M',
 'swamp-chest': 'Field_04E',
 'taltal-left-ascent-cave': 'Tamaranch02_01B',
 'taltal-ledge-chest': 'Field_02N',
 'taltal-5-chest-puzzle': 'Tamaranch05_04A',
 'taltal-west-chest': 'Field_02E',
 'villa-cave': 'RichardCave_01A',
 'woods-crossing-cave-chest': 'MysteriousWoodsCave01_02B',
 'woods-north-cave-chest': 'MysteriousWoodsCave02_01A',
 'woods-south-chest': 'Field_08B',
 'woods-north-chest': 'Field_05B',
 'D1-west-hallway': 'Lv01TailCave_05A',
 'D1-middle-ledge': 'Lv01TailCave_05D',
 'D1-3-of-a-kind': 'Lv01TailCave_05F',
 'D1-bomb-room': 'Lv01TailCave_06B',
 'D1-middle-kill-chest': 'Lv01TailCave_06C',
 'D1-spark-chest': 'Lv01TailCave_06D',
 'D1-button-chest': 'Lv01TailCave_07D',
 'D1-stalfos-chest': 'Lv01TailCave_07E',
 'D1-4-zols-chest': 'Lv01TailCave_08B',
 'D2-boos': 'Lv02BottleGrotto_02B',
 'D2-long-room-west': 'Lv02BottleGrotto_02C',
 'D2-long-room-east': 'Lv02BottleGrotto_02D',
 'D2-vacuum-mouth-room': 'Lv02BottleGrotto_03C',
 'D2-kill-puzzle': 'Lv02BottleGrotto_03F',
 'D2-west-chest': 'Lv02BottleGrotto_06B',
 'D2-entrance-chest': 'Lv02BottleGrotto_08C',
 'D2-single-shy-guy': 'Lv02BottleGrotto_08D',
 'D2-peg-circle': 'Lv02BottleGrotto_08E',
 'D2-button-chest': 'Lv02BottleGrotto_08F',
 'D3-north-chest': 'Lv03KeyCavern_01C',
 'D3-central-ledge': 'Lv03KeyCavern_02A',
 'D3-central-chest': 'Lv03KeyCavern_02C',
 'D3-east-ledge': 'Lv03KeyCavern_02D',
 'D3-hallway-4': 'Lv03KeyCavern_04B',
 'D3-hallway-3': 'Lv03KeyCavern_05B',
 'D3-hallway-2': 'Lv03KeyCavern_06B',
 'D3-hallway-side-room': 'Lv03KeyCavern_06C',
 'D3-hallway-1': 'Lv03KeyCavern_07B',
 'D3-vacuum-mouth': 'Lv03KeyCavern_08C',
 'D4-north-chest': 'Lv04AnglersTunnel_02D',
 'D4-east-side-north': 'Lv04AnglersTunnel_03G',
 'D4-east-side-south': 'Lv04AnglersTunnel_05G',
 'D4-west-ledge': 'Lv04AnglersTunnel_07C',
 'D4-east-of-puzzle': 'Lv04AnglersTunnel_04D',
 'D4-south-of-puzzle': 'Lv04AnglersTunnel_05C',
 'D4-central-room': 'Lv04AnglersTunnel_05D',
 'D4-small-island': 'Lv04AnglersTunnel_06F',
 'D4-ledge-north': 'Lv04AnglersTunnel_04F',
 'D4-statues-chest': 'Lv04AnglersTunnel_07F',
 'D4-lobby': 'Lv04AnglersTunnel_07E',
 'D4-crystals': 'Lv04AnglersTunnel_08E',
 'D5-past-master-stalfos-3': 'Lv05CatfishsMaw_01E',
 'D5-water-tunnel': 'Lv05CatfishsMaw_02E',
 'D5-right-side-north': 'Lv05CatfishsMaw_02G',
 'D5-right-side-middle': 'Lv05CatfishsMaw_03G',
 'D5-right-side-east': 'Lv05CatfishsMaw_03H',
 'D5-past-master-stalfos-1': 'Lv05CatfishsMaw_05G',
 'D5-west-chest': 'Lv05CatfishsMaw_06C',
 'D5-helmasaurs': 'Lv05CatfishsMaw_07D',
 'D5-west-stairs-chest': 'Lv05CatfishsMaw_08E',
 'D5-near-entrance': 'Lv05CatfishsMaw_08G',
 'D6-far-northwest': 'Lv06FaceShrine_02A',
 'D6-far-northeast': 'Lv06FaceShrine_02H',
 'D6-statue-line-north': 'Lv06FaceShrine_03B',
 'D6-statue-line-south': 'Lv06FaceShrine_04B',
 'D6-pot-chest': 'Lv06FaceShrine_03G',
 'D6-canal': 'Lv06FaceShrine_04G',
 'D6-3-wizzrobes': 'Lv06FaceShrine_05A',
 'D6-gated-hallway-north': 'Lv06FaceShrine_06C',
 'D6-gated-hallway-south': 'Lv06FaceShrine_07C',
 'D6-southwest-chest': 'Lv06FaceShrine_07B',
 'D6-wizzrobes-ledge': 'Lv06FaceShrine_07G',
 'D7-1f-west': 'Lv07EagleTower_07A',
 'D7-west-ledge': 'Lv07EagleTower_05A',
 'D7-east-ledge': 'Lv07EagleTower_05D',
 'D7-3ofakind-north': 'Lv07EagleTower_01B',
 'D7-2f-horseheads': 'Lv07EagleTower_01C',
 'D7-3ofakind-south': 'Lv07EagleTower_04B',
 'D7-blue-pegs-chest': 'Lv07EagleTower_03D',
 'D7-3f-horseheads': 'Lv07EagleTower_01G',
 'D7-grim-creeper': 'Lv07EagleTower_02H',
 'D8-far-northwest': 'Lv08TurtleRock_02A',
 'D8-far-northeast': 'Lv08TurtleRock_02H',
 'D8-left-exit-chest': 'Lv08TurtleRock_03C',
 'D8-dodongos': 'Lv08TurtleRock_03F',
 'D8-northern-ledge': 'Lv08TurtleRock_02E',
 'D8-beamos-chest': 'Lv08TurtleRock_04B',
 'D8-torches': 'Lv08TurtleRock_05B',
 'D8-west-roomba': 'Lv08TurtleRock_06B',
 'D8-surrounded-by-blocks': 'Lv08TurtleRock_06D',
 'D8-sparks-chest': 'Lv08TurtleRock_07B',
 'D8-east-of-pots': 'Lv08TurtleRock_07F',
 'D8-far-southwest': 'Lv08TurtleRock_08A',
 'D8-far-southeast': 'Lv08TurtleRock_08H',
 'D0-northern-chest': 'Lv10ClothesDungeon_04F',
 'D0-zol-pots': 'Lv10ClothesDungeon_05D',
 'D0-south-orbs': 'Lv10ClothesDungeon_07F',
 'D0-west-color-puzzle': 'Lv10ClothesDungeon_07D',
 'D0-putters': 'Lv10ClothesDungeon_08E'}


smallKeyRooms = {
 'D1-beetles': 'Lv01TailCave_08C',
 'D2-double-stalfos': 'Lv02BottleGrotto_07D',
 'D2-double-shy-guys': 'Lv02BottleGrotto_07F',
 'D3-pre-boss': 'Lv03KeyCavern_08G',
 'D3-triple-bombites': 'Lv03KeyCavern_01B',
 'D3-pairodds': 'Lv03KeyCavern_03A',
 'D3-five-zols': 'Lv03KeyCavern_04C',
 'D3-basement-north': 'Lv03KeyCavern_03G',
 'D3-basement-west': 'Lv03KeyCavern_04F',
 'D3-basement-south': 'Lv03KeyCavern_05G',
 'D4-sunken-item': 'Lv04AnglersTunnel_04E', # Also Lv04AnglersTunnel_06A, but leave vanilla for now.
 'D5-crystal-blocks': 'Lv05CatfishsMaw_01C',
 'D6-wizzrobe-pegs': 'Lv06FaceShrine_03D',
 'D6-tile-room': 'Lv06FaceShrine_05D',
 'D7-like-likes': 'Lv07EagleTower_08D',
 'D7-hinox': 'Lv07EagleTower_04A',
 'D8-gibdos': 'Lv08TurtleRock_03G',
 'D8-statue': 'Lv08TurtleRock_04C',
 'D8-west-vire': 'Lv08TurtleRock_06A',
 'D8-east-roomba': 'Lv08TurtleRock_07G',
 'D0-north-orbs': 'Lv10ClothesDungeon_05E',
 'D0-east-color-puzzle': 'Lv10ClothesDungeon_05F'
}