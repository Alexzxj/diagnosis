import operator

def hasKey(key, data):
    if(isinstance(data, dict)):
        if key in data.keys():
            return True
    return False

def hasKeyNotEmpty(key, data):
    """判断字典是否存在，并且非空"""
    if(hasKey(key, data) and data[key] != ""):
        return  True
    return  False

#获取格式化数据
def getFormatData(datas):
    if(datas == "" or len(datas) <= 0):
        return None

    colName = []
    rows = []
    isIDX = False
    try:
        for itemColumn in datas[0]:
            if(operator.eq(itemColumn,'IDX')):
                isIDX = True
                continue
            colName.append(itemColumn)

        for itemRow in datas:
            rowdata = []
            row = {}
            if(isIDX):
                row["rowName"] = itemRow["IDX"]
            else:
                row["rowName"] = 0
            for itemColumn in colName:
                rowdata.append(itemRow[itemColumn])

            row["rowData"] = rowdata
            rows.append(row)
    except Exception as e:
        pass

    return { "colName" : colName, "rows" : rows }

def getFormatRowToColumn(datas):
    if (datas == "" or len(datas) <= 0):
        return None

    colName = {}
    rows = []
    try:
        for itemColumn in datas[0]:
            if (operator.eq(itemColumn, 'IDX')):
                continue
            colName[itemColumn] = []

        for itemRow in datas:
            for itemColumn in colName:
                colName[itemColumn].append(itemRow[itemColumn])

        for item in colName:
            rows.append({"rowName" : item, "rowData" : colName[item]})


    except Exception as e:
        pass

    return { "rows" : rows }
