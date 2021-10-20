import oead

"""
# Find a struct in a 
def findStruct(sheet, field, value):
	for struct in sheet.values:
		if (field, value) in struct.items():
			return struct

	raise ValueError((field, value))


# Returns the value of a field given the field name.
def getFromStruct(struct, field):
	for item in struct.items():
		if item[0] == field:
			return item[1]

	raise ValueError(field)


# Updates and returns a struct with the field:value pairs from newFields
def updateStruct(struct, newFields):
	structDict = {f: v for f, v in struct.items()}

	for key, value in newFields.items():
		structDict[key] = value

	return oead.gsheet.Struct(structDict)
"""

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
