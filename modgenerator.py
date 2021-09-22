import yaml
import os
import re

import leb

def makeMod(placements, romPath, outdir):
	# Start by setting up the paths for the RomFS
	if not os.path.exists(f'{outdir}/Romfs/region_common/level'):
		os.makedirs(f'{outdir}/Romfs/region_common/level')

	placedBracelet = False

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

		if item == b'PowerBraceletLv1':
			if placedBracelet:
				item = b'PowerBraceletLv2'
			else:
				placedBracelet = True

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
