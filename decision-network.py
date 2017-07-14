import collections
import re
import math
import operator
import time

global topOrder, network
class Node:
    def __init__(self):
        self.name = ''
        self.parents = []
        self.table = collections.OrderedDict()
        self.type = ''

class Variable:
    def __init__(self):
        self.name = ''
        self.value = ''

def printQuery(qtype,queries,evidence):
    print "Query:",
    print qtype + " "

    print "queries: ",
    for q in queries:
        print q.name + q.value + ", ",

    print "evidence: ",
    for e in evidence.iterkeys():
        print e + evidence.get(e) + ", ",

    print

def ask(qtype, queries, evidence):
    global final_result, op_file
    result = 0
    if qtype == 'P':
        res = enumerateAsk(queries,evidence)
        i = ''
        for q in queries:
            if q.value == '+':
                i += '0'
            else:
                i += '1'
        resIdx = int(i,2)
        result = res[resIdx]
        result = round(result,2)
        result = format(result, '.2f')
        print >> op_file, result

    if qtype == 'EU':
        result = calcEU(queries,evidence)
        result = int(round(result))
        print >> op_file, result

    if qtype == 'MEU':
        calcMEU(queries, evidence)

def calcMEU(queries, evidence):
    global final_result
    size = int(math.pow(2,len(queries)))

    meu_table = [0]*size

    for i in range(0,size):
        new_queries = []
        index = str((bin(i)[2:]))
        index = index.zfill(len(queries))
        j=0
        for q in queries:
            qvar = Variable()
            qvar.name = q.name
            if index[j] == '0':
                qvar.value = '+'
            else:
                qvar.value = '-'
            j+=1
            new_queries.append(qvar)
        meu_table[i] = calcEU(new_queries,evidence)
    index, value = max(enumerate(meu_table), key=operator.itemgetter(1))

    value = int(round(value))

    index = str((bin(index)[2:]))
    index = index.zfill(len(queries))

    res = ""
    for z in range(0,len(queries)):
        if index[z] == '0':
            print >> op_file, '+',
        else:
            print >> op_file, '-',

    print >> op_file, value
    return

def calcEU(queries, evidence):
    for q in queries:
        evidence.update({q.name : q.value})

    ut = network.get('utility')
    ut_parents = ut.parents
    eu_queries = []
    given = []
    for p in ut_parents:
        if p not in evidence.iterkeys():
            v = Variable()
            v.name=p
            eu_queries.append(v)
        else:
            v = Variable()
            v.name=p
            v.value=evidence.get(p)
            given.append(v)
    result = enumerateAsk(eu_queries,evidence)
    size = int(math.pow(2,len(eu_queries)))

    sum = 0
    for i in range(0,size):
        index = str((bin(i)[2:]))
        index = index.zfill(len(eu_queries)-len(given))
        st = ''
        for j in range(0,len(ut_parents)-len(given)):
            if index[j] == '0':
                s = '+'
            else:
                s = '-'
            st += s
        for g in given:
            st += g.value
        st = str(st)
        sum += float(result[i]) * float(ut.table.get(st))

    return sum

def enumerateAsk(queries, evidence):
    global topOrder
    size = int(math.pow(2,len(queries)))
    probTable = [0]*size
    orderList = topOrder
    maxIndex = 0
    for e in evidence.iterkeys():
        if network.get(e).type != 'decision':
            if topOrder.index(e) > maxIndex:
                maxIndex = topOrder.index(e)
    for q in queries:
        if network.get(q.name).type != 'decision':
            if topOrder.index(q.name) > maxIndex:
                maxIndex = topOrder.index(q.name)
    orderList = topOrder[0:maxIndex+1]
    evid = dict(evidence)
    for i in range(0,size):
        index = str((bin(i)[2:]))
        index = index.zfill(len(queries))
        j = 0
        for v in queries:
            var = Variable()
            var.name = v.name
            if index[j] == '1':
                var.value = '-'
            else:
                var.value = '+'
            j+=1
            evid.update({var.name : var.value})
        order = list(orderList)
        prob = enumerateAll(order,evid)
        probTable[i] = prob
        print probTable
    resultTable = normalize(probTable)
    return resultTable

def normalize(table):
    sum = 0
    for val in table:
        sum += val
    if sum != 0:
        for i in range(0,len(table)):
            table[i] = table[i]/sum
    return table

def enumerateAll(vars, evidence):
    if(len(vars) == 0):
        return 1

    global network
    firstVar = vars.pop(0)
    #vars.remove(firstVar)
    sign = evidence.get(firstVar)
    varObj = network.get(firstVar)
    parents = varObj.parents
    if(firstVar in evidence.iterkeys()):
        if(len(parents) == 0):
            if sign == '+':
                pb = float(varObj.table.get(''))
            else:
                pb = 1 - float(varObj.table.get(''))
            if pb != 0:
                return pb*enumerateAll(vars, evidence)
            else:
                return 0
        else:
            keyIdx = ''
            for p in parents:
                keyIdx += evidence.get(p)

            if sign == '+':
                pb = float(varObj.table.get(keyIdx))
            else:
                pb = 1 - float(varObj.table.get(keyIdx))
            if pb!= 0:
                return pb*enumerateAll(vars, evidence)
            else:
                return 0


    domain = ['+','-']
    sum = 0
    ev = dict(evidence)

    for x in domain:
        vars_copy = list(vars)
        ev.update({firstVar:x})
        sign = x
        if(len(parents) == 0):
            if sign == '+':
                pb = float(varObj.table.get(''))
            else:
                pb = 1 - float(varObj.table.get(''))
        else:
            keyIdx = ''
            for p in parents:
                keyIdx += ev.get(p)

            if sign == '+':
                pb = float(varObj.table.get(keyIdx))
            else:
                pb = 1 - float(varObj.table.get(keyIdx))
        if pb != 0:
            sum += pb*enumerateAll(vars_copy,ev)
    return sum

def main():
    start = time.time()
    global topOrder, network, op_file, final_result
    op_file = open("output.txt", 'a')
    file = open("input23.txt", 'r')
    lines = file.read().splitlines()

    queryLines = []
    network = collections.OrderedDict()
    topOrder = []
    i = 0
    while(lines[i] != '******'):
        queryLines.append(lines[i])
        i=i+1

    i = i +1
    global flag
    flag = 0

    while i != len(lines):
        flag = 0
        dec = 0
        ut = 0
        n = Node()
        while lines[i] != '***' and lines[i] != '******':
            if flag == 0 :
                flag = 1
                line = lines[i].split('|')
                node = line[0].split(' ')
                n.name = node[0]
                if n.name == 'utility':
                    ut = 1
                if(len(line)) > 1:
                    parent = line[1].split(' ')
                    parent = filter(None, parent)
                    n.parents = parent
                i = i +1

            else:
                values = lines[i].split(' ')
                key = ''

                if(len(values) == 1 and values[0] == 'decision'):
                    n.table.update({key : 'decision'})
                    n.type = 'decision'
                    dec = 1

                for v in values:
                    if v == '+' or v == '-':
                        key = key + v
                n.table.update({key : values[0]})
                i = i+1
            if i == len(lines):
                break
        if(dec == 0 and ut == 0):
            topOrder.append(n.name)
        network.update({n.name:n})
        if i == len(lines):
            break
        i = i + 1

    for q in queryLines:
        queries = []
        evidence = collections.OrderedDict()
        qry = re.split(r'[()]',q)
        split = qry[1].split('|')
        vars = split[0].split(',')
        for var in vars:
            vlist = var.split(' ')
            vlist = filter(None, vlist)
            v = Variable()
            for c in vlist:
                if c != '=':
                    if c != '+' and c != '-':
                        v.name = c
                    else:
                        v.value = c
            queries.append(v)
        if(len(split) > 1):
            evi = split[1].split(',')
            for e in evi:
                elist = e.split(' ')
                elist = filter(None, elist)
                e = Variable()
                for c in elist:
                    if c != '=':
                        if c != '+' and c != '-':
                            e.name = c
                        else:
                            e.value = c
                evidence.update({e.name : e.value})
        ask(qry[0],queries,evidence)
    file.close()
    op_file.close()
    print time.time() - start

main()
