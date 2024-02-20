import pyjsparser as parser
from os import path


class Proxy:
    def __init__(self, name, url, hosts=[], nets=[], default=False):
        self.name = str(name)
        self.url = str(url)
        self.dnsDomainIs = list(hosts)
        self.isInNet = list(nets)
        self.default = bool(default)
 
def parsePACFile(file:str):
    error = None
    parsed = []
    with open(file) as f:
        try:
            parsed.append(parser.parse(f.read()))
        except Exception as error:
            return error, None
    f.close()
    return error, parsed

def findFunction(parsed:tuple, name:str):
    for block in parsed:
        if block is not None and block["type"] == "Program":
            for item in block["body"]:
                if item["type"] == "FunctionDeclaration" and item["id"]["name"] == name:
                    return item
    
def findProxyFunction(parsed:tuple):
    return findFunction(parsed, "FindProxyForURL")      

def returnFunctionContent(function:tuple):
    if function["body"]["type"] == 'BlockStatement':
        return function["body"]["body"]

def findIfStatements(content:list):
    ifs = []
    for c in content:
        if c["type"] == 'IfStatement':
            ifs.append(c)
    return ifs

def parseIfStatement(ifstatement:tuple, proxies:list=[]):
    if ifstatement["consequent"]["type"] == "BlockStatement" and ifstatement["consequent"]["body"][0]["type"] == "ReturnStatement":
        proxy = findProxy(proxies, ifstatement["consequent"]["body"][0]["argument"]["value"])
        parseFunctionTypes(ifstatement["test"], proxy)
    elif ifstatement["consequent"]["type"] == "ReturnStatement":
        proxy = findProxy(proxies, ifstatement["consequent"]["argument"]["value"])
        parseFunctionTypes(ifstatement["test"], proxy)

    return proxies        


def parseFunctionTypes(function:tuple, proxy:Proxy):
    if function["type"] == "CallExpression":
            if function["callee"]["name"] == "dnsDomainIs" :
                proxy.dnsDomainIs.append(function["arguments"][1]["value"])
            
            if function["callee"]["name"] == "isInNet" :
                proxy.isInNet.append(function["arguments"][1]["value"])
    
    if function["type"] == "BinaryExpression":
        ''' BinaryExpressions not implemeted '''

    if function["type"] == "LogicalExpression" and function["operator"] == "||":
        parseFunctionTypes(function["left"], proxy)
        parseFunctionTypes(function["right"], proxy)



def findProxy(proxies:list, proxyurl:str):
    for p in proxies:
        if p.url == proxyurl:
            return p
    
    proxy = Proxy(proxyurl.split(':')[0].replace("PROXY ",""), proxyurl,[])
    proxies.append(proxy)
    return proxy

#def checkPacFile(parsed:str):
#