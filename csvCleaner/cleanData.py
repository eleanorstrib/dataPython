import os
import csv
from collections import Counter


# This is for dealing with csv's that have forced empty cells in extra rows (non data, non header)
def nibble(row):
	nibbled_row = []
	save = False

	# first check if we want to nibble/trim this row
	# we don't want to nibble the header rows
	empties = 0
	for elem in reversed(row):
		if(getType(elem) == 'empty'):
			empties += 1
		else:
			break

	#  If less than half of cells at end of row are empty, we may have data or header
	if(empties < len(row)/2):
		return row

	# go ahead and nibble this row. It's not full data or heaader rows
	for elem in reversed(row):
		if(save == False):
			if getType(elem) == 'empty':
				continue
			else:
				save = True
				nibbled_row.append(elem)
		else:
			nibbled_row.append(elem)

	return nibbled_row[::-1]


# super simple type checking, anything other than int will be str
def getType(elem):
	if elem == '':
		return 'empty'

	try: 
		int(elem)
		return 'int'
	except ValueError:
	 	return 'str'


def getTypesPattern(row):
	rowTypes = []
	for elem in row:
		rowTypes.append(getType(elem))
	return rowTypes


def isRowEmpty(pattern):
	for elem in pattern:
		if elem != 'empty':
			return False
	return True


# ToDo: clean this up, so it returns fewer things!!!! 
def getPatterns(reader):
	# # get most common length of rows....this should be our data and useful header
	# # ToDo: think about more efficient way to do this
	row_lengths = []
	row_type_patterns = []
	rows = []
	for row in reader: 
		pattern = getTypesPattern(row)

		if isRowEmpty(pattern) == False:
			row = nibble(row)
			pattern = getTypesPattern(row)  # Do this more efficiently, instead of calling again.

			row_lengths.append(len(row))
			row_type_patterns.append(tuple(pattern))
			rows.append(row)
		
	counts = Counter(row_lengths)
	common_row_length = counts.most_common(1)[0][0]

	patternCounts = Counter(row_type_patterns)
	common_row_patterns = patternCounts.most_common()

	return rows, common_row_length, patternCounts, common_row_patterns



def getKeepRows(rows, common_row_length):
	# Save header and data rows 
	keepRows = []
	for row in rows:
		if len(row) == common_row_length:
			keepRows.append(row)

	return keepRows


def flattenHeaders(keepRows):
	# This is not as robust as it can be, keeping it simple for POC
	# Assumption: first rows are likely to be headers, and when pattern becomes 'common', it's data
	# Assumption: headers will not have integers as names --> header rows don't have int types in them
	headers = []
	for row in keepRows[:3]:
		if 'int' not in getTypesPattern(row):
			headers.append(row)
	

	if len(headers) > 1:
		# remove the old headers 
		keepRows = keepRows[len(headers):]

		new_header = []

		i = 0
		pre = ''
		post = ''
		for item in headers[0]:

			types = (getType(headers[0][i]), getType(headers[1][i]))

			if types == ('str', 'str'):
				pre = headers[0][i]
				post = " " + headers[1][i]
			if types == ('empty', 'str'):
				post = " " + headers[1][i]
			if types == ('str', 'empty'):
				pre = headers[0][i]
				post = ''
			if types == ('empty', 'empty'):
				pre = ''
				post = ''

			new_header.append(pre + post)
			i += 1

		keepRows.insert(0,new_header)

	return keepRows


def removeEmptyColumns(keepRows):
	#----------------------------------------------
	#  remove empty columns
	#  To Do: do this more efficiently!!
	header = keepRows[0]

	# find any empty header cells
	emptyHeaderCells = []
	i = 0
	for cell in header:
		if(getType(cell) == 'empty'):
			emptyHeaderCells.append(i)
		i += 1

	# check if all the data cells in column are also empty
	columns_to_remove = []
	for col in emptyHeaderCells:
		remove_col = True
		for row in keepRows:
			if getType(row[col]) != 'empty':
				remove_col = False
		if remove_col == True:
			columns_to_remove.append(col)


	# # Now go through and remove columns from header and data
	cleanRows = []
	for row in keepRows:
		tempRow = []
		i=0
		for elem in row:
			if i not in columns_to_remove:
				tempRow.append(elem)
			i+=1

		cleanRows.append(tempRow)

	return cleanRows



# ---------------------------------------------------------------------------------------
def cleanFile(file_name, dest_folder):
	file_path = file_name
	file_name = os.path.basename(file_name)
	file_name_short = os.path.splitext(file_name)[0]

	file = open(file_path, 'r')
	reader = csv.reader(file)


	rows, common_row_length, patternCounts, common_row_patterns = getPatterns(reader)

	keepRows = getKeepRows(rows, common_row_length)
	keepRows = flattenHeaders(keepRows)

	cleanRows = removeEmptyColumns(keepRows)	

	#----------------------------------------------
	# write out cleaned data into new csv file
	complete_name = os.path.join(dest_folder, file_name_short + '_cleaned.csv')
	with open( complete_name, 'wb') as f:
		writer = csv.writer(f)
		writer.writerows(cleanRows)

	print 'cleaned file: ', complete_name	

	f.close()

	file.close()