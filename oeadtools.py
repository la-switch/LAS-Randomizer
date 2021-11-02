import oead

def readSheet(sheetFile):
	with open(sheetFile, 'rb') as file:
		sheet = oead.gsheet.parse(oead.Bytes(file.read()))

	return {'alignment': sheet.alignment, 'hash': sheet.hash, 'name': sheet.name, 'root_fields': sheet.root_fields, 'values': sheet.values}


def writeSheet(sheetFile, sheet):
	newSheet = oead.gsheet.Sheet()
	newSheet.alignment = sheet['alignment']
	newSheet.hash = sheet['hash']
	newSheet.name = sheet['name']
	newSheet.root_fields = sheet['root_fields']

	newSheet.values = sheet['values']

	with open(sheetFile, 'wb') as file:
		file.write(newSheet.to_binary())


def parseStruct(struct):
	result = {}
	for k,v in struct.items():
		if type(v) == oead.gsheet.Struct:
			result[k] = parseStruct(v)
		else:
			result[k] = v

	return result


def dictToStruct(d):
	for k in d:
		if type(d[k]) == dict:
			d[k] = dictToStruct(d[k])

	return oead.gsheet.Struct(d)


# Return and create an empty structure for an element in the Conditions datasheet
# checks is a list of (category, paramter) tuples
def createCondition(name, checks):
	condition = {'symbol': name, 'conditions': oead.gsheet.StructArray()}
	for category, parameter in checks:
		condition['conditions'].append({'category': category, 'parameter': parameter})

	return condition