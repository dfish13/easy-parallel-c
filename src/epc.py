import re

def addOMPtags(code, filename): 
    # print(code)
    # pattern = re.compile(r"for\s*\((.*)\)\s*\{([^\}]*)\}")
    # result = pattern.match(code)
    result = re.findall(r"(for\s*\((.*);(.*);(.*)\)\s*\{([^\}]*)\})", code)

    taggedCode = code

    j = 0
    parallelizedLoops = 0
    while (j < len(result)): 
        loop = result[j]
        iteratorsCode = loop[3]
        iteratorVariables = detectIncrementVariables(iteratorsCode)
        conditionsCode = loop[2]
        sharedVariables = findSharedVariablesOnHeader(conditionsCode, iteratorVariables)
        privateVariables = iteratorVariables
        sentencesCode = loop[4]
        sentences = separateSentences(sentencesCode)
        variables = findVariablesAndOperators(sentences, privateVariables, sharedVariables)
        if (variables != False):
            print("Variables identified for OpenMP tag generation: ")
            print(variables)
            statementPos = taggedCode.find(loop[0])
            i = statementPos - 1
            found = False
            tabs = ""
            while (i >= 0 and not found): 
                if (taggedCode[i] != "\n"): 
                    tabs = taggedCode[i] + tabs
                else: 
                    found = True
                i -= 1
            tag = "#pragma parallel default(none) "
            if (len(variables["shared"]) > 0):
                tag += "shared(" + stringifyVariableList(variables["shared"]) + ") "
            if (len(variables["private"]) > 0):
                tag += "private(" + stringifyVariableList(variables["private"]) + ") "
            if (len(variables["reduction"]) > 0): 
                tag += "reduction(" + stringifyVariableList(variables["reduction"]) + ")"
            tag += "\n" + tabs + "{\n"
            lines = loop[0].split("\n")
            block = tabs
            for line in lines: 
                block += tabs + "\t" + line + "\n"
            taggedCode = taggedCode[:statementPos] + tag + block + tabs + "}" + taggedCode[statementPos + len(loop[0]):]
            parallelizedLoops += 1

        j += 1
    if (parallelizedLoops == 0): 
        print("-- The code cannot be parallelized. --")
    else: 
        include = "#include <omp.h>\n"
        taggedCode = include + taggedCode 
        file = open(filename[:-2] + ".omp.c", "w")
        file.write(taggedCode)
        file.close()
        print("-- OpenMP tags inserted successfully. --")


def stringifyVariableList(variables): 
    result = ""
    i = 0
    for key, variable in variables.items():   
        if (variable["type"] == "reduction" and "operator" in variable): 
            result += variable["operator"] + ": " 
        result += variable["value"]
        if (i < len(variables) - 1): 
            result += ", "
        i += 1
    return result

def detectIncrementVariables(code): 
    operators = ["-", "+", "*", "/", "%", "<", ">", " and ", " or ", " not ", "!", " in ", " is ", "&", "|", "^"]
    code = code.strip()
    sentences = code.split(",")
    result = []
    for sentence in sentences: 
        components = sentence.split("=");         
        incrementVar = components[0]
        for operator in operators:
            incrementVar = incrementVar.replace(operator, "")
        operator = operator.strip()
        if ("(" in operator): 
            raise Exception("Could not identify the variable modified by the loop")
        result.append(incrementVar)  
    return result

def separateSentences(code):
    code = code.strip()
    sentences = code.split(";")
    result = []
    for sentence in sentences: 
        sentence = sentence.strip()
        if (sentence != ""):
            result.append(sentence)
    return result

def findVariablesAndOperators(sentences, incrementVars, sharedVars): 
    operators = ["-", "+", "*", "/", "%", "&", "|", "^"]
    result = {
        "shared": sharedVars,
        "private": {}, 
        "reduction": {},
        "independent": {},
    }
    parallelizableSentences = 0
    for sentence in sentences: 
        components = sentence.split("=")
        assignedVar = components[0].strip()
        assignedVarObj = {
            "value": assignedVar,
        }
        i = 0
        found = False
        while (i < len(operators) and not found): 
            if (assignedVar[len(assignedVar) - 1] == operators[i]): 
                assignedVarObj = {
                    "value": assignedVar[:-1].strip(), 
                    "operator": operators[i]
                }
                found = True
            i += 1

        processedVar = processVar(assignedVarObj, incrementVars)
        if (processedVar):
            result[processedVar["type"]][processedVar["value"]] = processedVar
            sharedVariable = extractSharedVariable(processedVar)
            if (sharedVariable): 
                result[sharedVariable["type"]][sharedVariable["value"]] = sharedVariable

        operands = components[1].strip()
        functionCallCheck = re.findall(r"([a-zA-Z]+\w*\([^)]*\))", operands) 
        if (len(functionCallCheck) > 0): 
            return False
        operandItems = separateOperands(operands, operators)

        numIndependentOperators = 0
        independentOperandPresent = False
        for operand in operandItems:             
            operandObj = {
                "value": operand
            }
            operandObj = processVar(operandObj, incrementVars)
            if (operandObj): 
                result[operandObj["type"]][operandObj["value"]] = operandObj
                if (operandObj["type"] == "independent"): 
                    numIndependentOperators += 1
                    sharedVariable = extractSharedVariable(operandObj)
                    result[sharedVariable["type"]][sharedVariable["value"]] = sharedVariable
            else: 
                numIndependentOperators += 1

        for reductionVar in result["reduction"]: 
            if (reductionVar in result["shared"]): 
                del result["shared"][reductionVar]
                

        if (numIndependentOperators == len(operandItems) or processedVar["type"] == "independent"): 
            parallelizableSentences += 1


        #TODO: check whether the assigned var is inside the assignments, then make it dependent and find the operator

    for incrementVar in incrementVars: 
        incrementVarObj = {
            "value": incrementVar, 
            "type": "private",
        }
        result["private"][incrementVarObj["value"]] = incrementVarObj    
    if (parallelizableSentences > 0):
        return result
    else: 
        return False

def findSharedVariablesOnHeader(operands, incrementVars): 
    operators = ["==", "<", ">", "<=", ">=", "-", "+", "*", "/", "%", "&", "|", "^"]
    result = {}
    operandItems = separateOperands(operands, operators)
    for operandItem in operandItems: 
        operandObj = {
            "value": operandItem
        }
        processedVar = processVar(operandObj, incrementVars)
        if (processedVar): 
            sharedVar = extractSharedVariable(processedVar)
            if (sharedVar): 
                result[sharedVar["value"]] = sharedVar
    return result
         
def separateOperands(operands, operators): 
    operandItems = [ operands ]
    for operator in operators: 
        newOperandItems = []
        for operandItem in operandItems: 
            splittedItems = operandItem.split(operator)
            for splittedItem in splittedItems: 
                newOperandItems.append(splittedItem.strip())
        operandItems = newOperandItems
    return operandItems


def processVar(variable, incrementVars):
    if (not variable["value"] in incrementVars): 
        if (variable["value"].find("(") >= 0): 
            return False
        detectVariable = re.findall(r"[0-9]*\.?[0-9]+", variable["value"])
        if (len(detectVariable) != 0): #operand is a number
            return False
        detectIndexes = re.findall(r"(\w)(\[\w\])+", variable["value"])
        if (len(detectIndexes) > 0): 
            variable["type"] = "independent"
        elif ("operator" in variable):
            variable["type"] = "reduction"
        else: 
            variable["type"] = "shared"
    else: 
        return False
    return variable

def extractSharedVariable(variable): 
    detectVariable = re.findall(r"(\w)(\[\w\])+", variable["value"])
    if (len(detectVariable) > 0):
        variable = {
            "value": detectVariable[0][0],
            "type": "shared",
        }
        return variable
    return False