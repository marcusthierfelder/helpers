import argparse
import xml.etree.ElementTree as ET
import sys
from operator import is_not
from functools import partial
from enum import Enum

class Modus(Enum):
    NONE = "none"
    LENGTH = "length"
    LABORBAR = "laborbar"


# ---------------------------------
def find_CustomView(root, page):
    outletName = 'nonBlankoNonImpactView' + page.__str__()
    destination = find_CustomViewOutlet_destination(root, outletName)
    if not destination:
        sys.exit("kein Outlet auf " + outletName)

    view = find_destination(root, destination)
    if not view:
        sys.exit("der outletView wurde nicht gefunden")

    return view


def find_CustomViewOutlet_destination(node, outletName):
    connections = node.find("objects").find("customObject").find("connections")
    for con in connections:
        if outletName == con.get("property"):
            return con.get("destination")
    return None


def find_destination(node, destination):
    id = node.get("id")
    if id == destination:
        return node
    else:
        for sub in node:
            v = find_destination(sub, destination)
            if v:
                return v
        return None


# ---------------------------------
def deep_search(node, xoff, yoff, hPage, wPage, cmFactor, hline):
    ret = []
    customClass = str(node.get('customClass') or '')

    if customClass == "ZSFormTextField":
        ret.append(parse_ZSFormTextField(node, xoff, yoff,  hPage, wPage, cmFactor, hline))
    elif customClass == "ZSFormGeschlechtPopUpBotton":
        ret.append(parse_ZSFormPopUpButton(node, xoff, yoff,  hPage, wPage, cmFactor, hline))
    elif customClass == "ZSRadioButton":
        ret.append(parse_ZSRadioButton(node, xoff, yoff,  hPage, wPage, cmFactor, hline))
    elif customClass.startswith("ZSFormTextView"):
        ret.append(parse_ZSFormTextView(node, xoff, yoff, hPage, wPage, cmFactor, hline))
    elif customClass == "ZSFormCommonKBVHeader":
        ret.append(parse_header(node, xoff, yoff, hPage, wPage, cmFactor, hline))
    elif customClass == "ZSCommonArztStempelImageView":
        ret.append(parse_stempel(node, xoff, yoff, hPage, wPage, cmFactor, hline))
    elif customClass == "ZSFormDateViewWithDirektdruckModification":
        ret.append(parse_ZSFormTextView(node, xoff, yoff, hPage, wPage, cmFactor, hline))
    elif customClass.startswith("ZSForm"):
        sys.exit(customClass + " muss noch implementiert werden")
    else:
        rect = node.find('rect')
        if rect is not None:
            xoff += float(rect.get('x'))
            yoff += float(rect.get('y'))
        for sub in node:
            subs = deep_search(sub, xoff, yoff, hPage, wPage, cmFactor, hline)
            if subs:
                ret.extend(subs)

    return ret


# ---------------------------------
def parse_ZSFormTextField(node, xoff, yoff, hPage, wPage, cmFactor, hline):
    keypath = get_value_binding(node, 'value')
    if keypath:
        if keypath.startswith("formular.checkbox"):
            return parse_TextField(node, xoff, yoff, hPage, wPage, cmFactor, hline, keypath, Modus.NONE)
        else:
            return parse_TextField(node, xoff, yoff, hPage, wPage, cmFactor, hline, keypath, Modus.LENGTH)
    else:
        #sys.exit('kein get_value_binding')
        return None

def parse_ZSRadioButton(node, xoff, yoff, hPage, wPage, cmFactor, hline):
    keypath = get_value_binding(node, 'value')

    rtas = node.find('userDefinedRuntimeAttributes')
    if rtas is not None:
        for rta in rtas:
            if rta.get('keyPath') == 'checkedCharacter':
                return parse_TextField(node, xoff, yoff, hPage, wPage, cmFactor, hline, keypath, Modus.LABORBAR)

    return parse_TextField(node, xoff, yoff, hPage, wPage, cmFactor, hline, keypath, Modus.NONE)


def parse_ZSFormPopUpButton(node, xoff, yoff, hPage, wPage, cmFactor, hline):
    keypath = get_value_binding(node, 'selectedValue')
    return parse_TextField(node, xoff, yoff, hPage, wPage, cmFactor, hline, keypath, Modus.NONE)


def parse_TextField(node, xoff, yoff, hPage, wPage, cmFactor, hline, keypath, modus):
    rect = node.find("rect")
    x = (xoff + float(rect.get("x"))) * cmFactor
    y = (hPage - (yoff + float(rect.get("y")))) * cmFactor
    w = float(rect.get("width")) * cmFactor

    if modus == Modus.LENGTH:
        line = construct_line4(x, y, w, keypath)
    if modus == Modus.LABORBAR:
        line = construct_line3lb(x, y, keypath)
    else:
        line = construct_line3(x, y, keypath)

    return {'x': x, 'y': y, 'line': line}

# ---------------------------------
def parse_ZSFormTextView(node, xoff, yoff, hPage, wPage, cmFactor, hline):
    rect = node.find("rect")
    x = (xoff + float(rect.get("x"))) * cmFactor
    w = float(rect.get("width")) * cmFactor
    h = float(rect.get("height")) * cmFactor
    lines = max( int( h/hline + 0.5 ) , 1)

    firstLineIdent = 0
    attrs = node.find("userDefinedRuntimeAttributes")
    if attrs:
        for attr in attrs:
            keypath = attr.get("keyPath")
            if keypath == "firstLineIdent":
                firstLineIdent =  float(attr.find("integer").get("value")) * cmFactor

    keypath = get_value_binding(node, 'value')

    if lines>1:
        y = (hPage - (yoff + float(rect.get("y")) + float(rect.get("height")))) * cmFactor + hline
        if firstLineIdent and firstLineIdent>0:
            line = construct_line6(x, y, w, lines, firstLineIdent, keypath)
        else:
            line = construct_line5(x, y, w, lines, keypath)
    else:
        y = (hPage - (yoff + float(rect.get("y")))) * cmFactor
        line = construct_line4(x, y, w, keypath)

    return {'x': x, 'y': y, 'line': line}


# ---------------------------------
def parse_header(node, xoff, yoff, hPage, wPage, cmFactor, hline):
    rect = node.find("rect")
    x = 1.0
    y = 0.5
    line = '[zsnd addKBVHeader:self.formular andPosX:{:2.2f} andPosY:{:2.2f}];'.format(x, y)
    return {'x': 0, 'y': 0, 'line': line}


def parse_stempel(node, xoff, yoff, hPage, wPage, cmFactor, hline):
    rect = node.find("rect")
    x = (xoff + float(rect.get("x"))) * cmFactor
    y = (hPage - (yoff + float(rect.get("y")) + float(rect.get("height"))) ) * cmFactor
    line = '[zsnd addArztStempel:self.formular andPosX:{:2.2f} andPosY:{:2.2f}];\n'.format(x, y)
    return {'x': 0, 'y': 1, 'line': line}


# ---------------------------------
def get_value_binding(node, name):
    cons = node.find("connections")
    if cons:
        for con in node.find("connections"):
            if con.get('name') == name:
                return con.get('keyPath')
    else:
        #sys.exit('kein value binding')
        return None


def construct_line3(x, y, keypath):
    return '[zsnd addLineAbsolute:[self valueForKeyPath:ZSnoLS(@"{}")] andPx:{:2.2f} andPy:{:2.2f} andFS:10];'.format(keypath, x, y)


def construct_line3lb(x, y, keypath):
    return '[zsnd addLaborBarAbsolute:[self valueForKeyPath:ZSnoLS(@"{}")] andPx:{:2.2f} andPy:{:2.2f} andFS:10];'.format(keypath, x, y)


def construct_line4(x, y, w, keypath):
    return '[zsnd addLineAbsolute:[self valueForKeyPath:ZSnoLS(@"{}")] andPx:{:2.2f} andPy:{:2.2f} andFS:10 andLength:{:2.2f}];'.format(
        keypath, x, y, w)


def construct_line5(x, y, w, lines, keypath):
    return '[zsnd addLineAbsolute:[self valueForKeyPath:ZSnoLS(@"{}")] andPx:{:2.2f} andPy:{:2.2f} andFS:10 andLineHeigth:0.85 andLength:{:2.2f} andMaxLines:{}];'.format(
        keypath, x, y, w, lines)


def construct_line6(x, y, w, lines, firstLineIdent, keypath):
    return '[zsnd addLineAbsolute:[self valueForKeyPath:ZSnoLS(@"{}")] andPx:{:2.2f} andPy:{:2.2f} andFS:10 andLineHeigth:0.85 andLength:{:2.2f} andMaxLines:{} andIndent:{:2.2f}];'.format(
        keypath, x, y, w, lines, firstLineIdent)



# ---------------------------------
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Arguments for xib2nadel")
    parser.add_argument('file', type=str, help="xib Datei")
    parser.add_argument('size', type=str, help="DIN Größe", choices=['A4', 'A5'])
    parser.add_argument('format', type=str, help="Format ", choices=['h', 'q'])
    args = parser.parse_args()


    # allgemeine Werte
    hPageA4 = 1244.
    wPageA4 = 882.
    cmFactor = 29.7 / hPageA4
    # oder cmFactor = 21.0 / wPageA4
    hline = 0.85

    if args.size == 'A4' and args.format == 'h':
        hPage = hPageA4
        wPage = wPageA4
    elif args.size == 'A4' and args.format == 'q':
        hPage = hPageA4
        wPage = wPageA4
    elif args.size == 'A5' and args.format == 'h':
        hPage = wPageA4
        wPage = hPageA4/2
    elif args.size == 'A5' and args.format == 'q':
        hPage = hPageA4/2
        wPage = wPageA4
    else:
        parser.print_help(sys.stderr)
        sys.exit("size format kombination nocht nicht implementiert  ")

    root = ET.parse(args.file).getroot()
    for page in range(1,8):
        view = find_CustomView(root, page)
        if not view:
           continue
        myList = deep_search(view, 0., 0., hPage, wPage, cmFactor, hline)


        prefix = """
-(BOOL) printWithSerialPrinter:(Drucker*) selectedPrinter
{
    ZSAssert(selectedPrinter.isSerialPrinter);    
    ZSNadeldrucker* zsnd = [ZSNadeldrucker instanceWithDrucker:selectedPrinter];
    """
        postfix = """
    return [zsnd printAll];
}
    """

        myList.append({'x':0, 'y':-1, 'line':prefix})
        myList.append({'x':0, 'y':9999, 'line':postfix})

        filter_null = partial(filter, partial(is_not, None))
        myList = list(filter_null(myList))

        sortedlist = sorted(myList, key=lambda elem: "%05.2f %05.2f" % (elem['y'], elem['x']))

        for elem in sortedlist:
            print("    " + elem.get('line'))