'''
convert-pac-traffpol
Tool for converting Javascript PAC file into Netscaler trafficpolicies with patternsets.
Today only "dnsDomainIs" directive in PAC file and first default proxy is supported. All other directives are ignored.
Please check output.
'''

import pyjsparser as parser
from os import path
from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askopenfile, asksaveasfile 
from tkinter import messagebox 
try:
    import pyi_splash
except ImportError or ModuleNotFoundError:
    pass

# define proxy class which holds URL and targets
class Proxy:
    def __init__(self, name, url, hosts=[], nets=[], default=False):
        self.name = str(name)
        self.url = str(url)
        self.hosts = list(hosts)
        self.nets = list(nets)
        self.default = bool(default)
 
def parsePACFile(file:str):
    error = None
    with open(file) as f:
        try:
            parsed = parser.parse(f.read())
        except Exception as error:
            return error, None
    f.close()
    return error, parsed

def returnProxy(proxies:list, proxyurl:str):
    for p in proxies:
        if p.url == proxyurl:
            return p
    
    proxy = Proxy(proxyurl.split(':')[0],proxyurl,[])
    proxies.append(proxy)
    return proxy

def netscalerConfig(proxies:list):
    conf = []
    for p in proxies:
        conf.append('######### PROXY %s ##########' % p.name)
        conf.append('add vpn trafficAction traffact_{name} http -proxy https://{url}'.format(name=p.name, url=p.url))

        if p.default == True:
            conf.append('add vpn trafficPolicy traffpol_{fname} true'.format(fname=p.name.replace('.','_')))
        else: 
            conf.append('add policy patset patset_proxy_{name} -comment "patternset for domains used with proxy {url}"'.format(name=p.name.replace('.','_'), url=p.url))
            for host in p.hosts:
                conf.append('bind policy patset patset_proxy_{name} {host}'.format(name=p.name.replace('.','_'), host=host))

        conf.append('add vpn trafficPolicy traffpol_{fname}  "HTTP.REQ.HOSTNAME.SET_TEXT_MODE(IGNORECASE).CONTAINS_ANY(\\"patset_proxy_{fname}\\")" traffact_{name}'.format(fname=p.name.replace('.','_'), name=p.name))
        conf.append('')
    return conf

def netscalerConfFile(proxies:list, file:str):
    f = open(file, 'w')
    f.writelines('\n'.join(netscalerConfig(proxies)))
    f.close()

def listingFiles(proxies:list, prefix:str=''):
    for p in proxies:
        if p.default: continue
        f = open(prefix + p.name.replace('.','_') + '.txt', 'w')
        f.writelines('\n'.join(p.hosts))
        f.close()

def getProxiesFromPacFile(file:str):
    error, parsed = parsePACFile(file)
    if error == None:
        proxies = getProxiesFromPac(parsed)
    else:
        proxies = None
    return error, proxies

def getProxiesFromPac(parsed:dict, proxies:list=[]):
    for rule in parsed['body'][0]['body']['body']:
        if rule['type'] == 'IfStatement' and rule['consequent']['argument']['value'].startswith('PROXY'):
            url = rule['consequent']['argument']['value'].replace('PROXY ','')
            proxy = returnProxy(proxies,url)
            t = rule['test']
            if 'callee' in t:
                if t['callee']['name'] in ['dnsDomainIs']:
                        proxy.hosts.append(t['arguments'][1]['value'])
            while 'left' in t: 
                if 'arguments' in t['left']:
                    if t['left']['callee']['name'] in ['dnsDomainIs']:
                            proxy.hosts.append(t['left']['arguments'][1]['value'])
                if 'arguments' in t['right']:
                    if t['right']['callee']['name'] in ['dnsDomainIs']:
                            proxy.hosts.append(t['right']['arguments'][1]['value'])
                t = t['left']
            
            # remove duplicates
            nhosts =  list(dict.fromkeys(proxy.hosts))
            proxy.hosts = nhosts
        elif rule['type'] == 'ReturnStatement' and rule['argument']['value'].startswith('PROXY'):
            # default rule
            proxies.append(Proxy(name='DEFAULT', url=rule['argument']['value'].replace('PROXY ','').split(';')[0], hosts=[], default=True))

    return proxies

def openGui():
    info = '''
Tool for converting Javascript PAC file into Netscaler trafficpolicies with patternsets.
The only supported PAC file directive is "dnsDomainIs" as well as first default proxy. 
All other directives are ignored.
Please check output before using it.
    '''

    win = Tk()
    win.geometry('700x300')
    win.title("PAC FILE CONVERTER")

    def open_file():
        ifile = askopenfile(mode ='r').name
        ifentry.delete(0, END)
        ifentry.insert(0, ifile)

    def save_file(): 
        ofile = asksaveasfile().name
        ofentry.delete(0, END)
        ofentry.insert(0, ofile)

    def convert_file():
        inp = ifentry.get()
        out = ofentry.get()
        if not path.lexists(path.dirname(inp)) or not path.lexists(path.dirname(out)):
                guiMsg("Please specify valid input AND output!")
        else:
            error, proxies = getProxiesFromPacFile(inp)
            if error == None:
                netscalerConfFile(proxies, out)
                guiMsg("NetScaler batch file is saved under\n" + out)
            else:
                guiMsg("Error in input file:\n" + str(error))

    Label(win, text = info, background="lightgray", width = 100, justify="center").place(x = 40, y = 10)

    Label(win, text = "PAC File: \t\t\n (Input)").place(x = 40, y = 120)
    ifentry = Entry(win, width = 60)
    ifentry.place(x = 160, y = 120) 
    Button(win, text ='Open', command = lambda:open_file()).place(x = 550, y = 120)

    Label(win, text = "Netscaler Batchfile: \t\n (Output)").place(x = 40, y = 160)
    ofentry = Entry(win, width = 60)
    ofentry.place(x = 160, y = 160) 
    Button(win, text ='SaveAs', command = lambda:save_file()).place(x = 550, y = 160)

    Button(win, text ='CONVERT', command = lambda:convert_file()).place(x = 40, y = 250)
    Button(win, text ='EXIT', command = win.destroy).place(x = 550, y = 250)

    win.mainloop()

def guiMsg(msg):
    messagebox.showwarning("Information", msg)

def main():
    try:
        pyi_splash.close()
    except:
        pass
    openGui()

### main ###
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)



