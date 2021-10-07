import yaml
import os
import re
import copy

import leb
import eventtools

def makeMod(placements, romPath, outdir):
    makeMarinTarinFix(romPath, outdir)
    makeStaticEventChanges(romPath, outdir)

    if 'free-book' in placements['settings']:
        setFreeBook(romPath, outdir)

    makeChestContentFixes(placements, romPath, outdir)



# Patch LEB files of rooms with chests to update their contents
def makeChestContentFixes(placements, romPath, outdir):
	# Start by setting up the paths for the RomFS
	if not os.path.exists(f'{outdir}/Romfs/region_common/level'):
		os.makedirs(f'{outdir}/Romfs/region_common/level')

	# Load the Items YAML. This is necessary to translate our naming conventions for the logic into the internal item names.
	with open("items.yml", 'r') as itemsFile:
		itemDefs = yaml.safe_load(itemsFile)
	
	seashellIndices = [2, 3, 12, 17, 22, 23, 24, 25] # hard-coded kinda hacky thing for chest-only rando

	for room in chestRooms:
		dirname = re.match('(.+)_\\d\\d[A-P]', chestRooms[room]).group(1)
		if not os.path.exists(f'{outdir}/Romfs/region_common/level/{dirname}'):
			os.makedirs(f'{outdir}/Romfs/region_common/level/{dirname}')

		with open(f'{romPath}/region_common/level/{dirname}/{chestRooms[room]}.leb', 'rb') as roomfile:
			roomData = leb.Room(roomfile.read())

		item = bytes(itemDefs[placements[room]]['item-key'], 'utf-8')
		seashellIndex = -1

		if placements[room] == 'seashell':
			seashellIndex = seashellIndices.pop()

		for i in range(5 if room == 'taltal-5-chest-puzzle' else 1): # use this to handle one special case where we need to write the same data to 5 chests in the same room
			if seashellIndex > -1:
				roomData.setChestContent(item, i, seashellIndex)
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
				roomData.setChestContent(item, 0, seashellIndex)
			else:
				roomData.setChestContent(item)

			with open(f'{outdir}/Romfs/region_common/level/Lv07EagleTower/Lv07EagleTower_06H.leb', 'wb') as outfile:
				outfile.write(roomData.repack())

		if room == 'D7-3f-horseheads':
			with open(f'{romPath}/region_common/level/Lv07EagleTower/Lv07EagleTower_05G.leb', 'rb') as roomfile:
				roomData = leb.Room(roomfile.read())

			item = bytes(itemDefs[placements[room]]['item-key'], 'utf-8')

			if placements[room] == 'seashell':
				roomData.setChestContent(item, 0, seashellIndex)
			else:
				roomData.setChestContent(item)

			with open(f'{outdir}/Romfs/region_common/level/Lv07EagleTower/Lv07EagleTower_05G.leb', 'wb') as outfile:
				outfile.write(roomData.repack())

# Fix the MarinTarinHouse room so that you can leave without having the shield
def makeMarinTarinFix(romPath, outdir):
    # Make sure the folder exists
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

# Make changes to some events that should be in every seed, e.g. setting flags for having watched cutscenes
def makeStaticEventChanges(romPath, outdir):
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

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/PlayerStart.bfevfl', playerStart)

    #################################################################################################################################
    ### TreasureBox event: Adds in events to make the Power Bracelets be progressive. Will extend to other items later.
    treasureBox = eventtools.readFlow(f'{romPath}/region_common/event/TreasureBox.bfevfl')

    # Add the EventFlags actor and the AddItem action to the Inventory actor.
    treasureBox.flowchart.actors.append(eventFlagsActor)
    eventtools.addActorAction(eventtools.findActor(treasureBox.flowchart, 'Inventory'), 'AddItem')
    inventoryActor = eventtools.findActor(treasureBox.flowchart, 'Inventory') # Store this actor to add to another flow.

    braceletLv1AddEvent = eventtools.createActionEvent(treasureBox.flowchart, 'Inventory', 'AddItem', {'itemType': 14, 'count': 1, 'autoEquip': False})
    braceletLv1GetSeqEvent = eventtools.createActionEvent(treasureBox.flowchart, 'Link', 'GenericItemGetSequenceByKey', {'itemKey': 'PowerBraceletLv1', 'keepCarry': False, 'messageEntry': ''}, braceletLv1AddEvent)

    braceletLv2AddEvent = eventtools.createActionEvent(treasureBox.flowchart, 'Inventory', 'AddItem', {'itemType': 15, 'count': 1, 'autoEquip': False})
    braceletLv2GetSeqEvent = eventtools.createActionEvent(treasureBox.flowchart, 'Link', 'GenericItemGetSequenceByKey', {'itemKey': 'PowerBraceletLv2', 'keepCarry': False, 'messageEntry': ''}, braceletLv2AddEvent)

    braceletGetFlagSetEvent = eventtools.createActionEvent(treasureBox.flowchart, 'EventFlags', 'SetFlag', {'symbol': 'unused0358', 'value': True}, braceletLv1GetSeqEvent) 

    braceletGetFlagCheckEvent = eventtools.createSwitchEvent(treasureBox.flowchart, 'EventFlags', 'CheckFlag', {'symbol': 'unused0358'}, {0: braceletGetFlagSetEvent, 1: braceletLv2GetSeqEvent})

    ChestContentCheckEvent = eventtools.createSwitchEvent(treasureBox.flowchart, 'FlowControl', 'CompareString', {'value1': eventtools.findEvent(treasureBox.flowchart, 'Event33').data.params.data['value1'], 'value2': 'PowerBraceletLv1'}, {0: braceletGetFlagCheckEvent, 1: 'Event33'})

    eventtools.insertEventAfter(treasureBox.flowchart, 'Event32', ChestContentCheckEvent)

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/TreasureBox.bfevfl', treasureBox)

    #################################################################################################################################
    ### Owl event: Modify the Eighth cutscene to give the ghost bottle.
    owl = eventtools.readFlow(f'{romPath}/region_common/event/Owl.bfevfl')

    owl.flowchart.actors.append(inventoryActor)
    eventtools.addActorAction(inventoryActor, 'AddBottle')
    eventtools.addActorAction(eventtools.findActor(owl.flowchart, 'Link'), 'GenericItemGetSequence')

    eventtools.createActionChain(owl.flowchart, 'Event34', [
        ('Inventory', 'AddBottle', {'index': 0}),
        ('Link', 'GenericItemGetSequence', {'itemType': 64, 'keepCarry': False, 'messageEntry': ''}),
        ('Owl', 'Destroy', {})
        ])

    eventtools.writeFlow(f'{outdir}/Romfs/region_common/event/Owl.bfevfl', owl)

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


# Set the event for the book of shadows to reveal the egg path without having the magnifying lens
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
