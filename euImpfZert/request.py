import requests
import sys
import logging
import http.client
from urllib import parse
from requests_pkcs12 import get,post
import urllib3

import xml.etree.ElementTree as ET
from xml.dom import minidom
from lxml import etree
import re
from io import StringIO

import base64
import string
import random
import hashlib
import os
from subprocess import PIPE, Popen
import json
import ast


#################
# DEGBUG sachen
http.client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



#################
# DATEN müssen hier angepasst werden

connector = "10.100.9.166"
connectorTLS = True
mandant = "TOMEDO2RU"
client = "TOMEDOKIM"
workplace = "WorkplaceKIM"
user = "test"

pkcs12_filename = 'clientCert.p12'
pkcs12_password = '123456'

genesenZert = False
serverType = "RU"   # PU RU SIMPLE





#################
# 
if connectorTLS:
    connectorURL = "https://" + connector + ":443"
else:
    connectorURL = "http://" + connector + ":80"


if serverType == "PU":
    server = "https://id.impfnachweis.info"
    realm = "bmg-ti-certify"
    client_id = "user-access-ti"
    issuer = "https://api.impfnachweis.info/api/certify/v2/issue"
elif serverType == "RU":
    server = "https://id.ru.impfnachweis.info"
    realm = "bmg-ti-certify"
    client_id = "user-access-ti"
    issuer = "https://api.ru.impfnachweis.info/api/certify/v2/issue"
elif serverType == "SIMPLE":
    server = "https://keycloak-cert-auth.dev.ibmega.net"
    realm = "master"
    client_id = "cert-auth"
    issuer = "https://api.ru.impfnachweis.info/api/certify/v2/issue"
else:
    print("nope:  falscher modus")
    sys.exit()




###############################
# schritt 1 und 2. -> Receive Challenge

def getChallenge(nonce):

    url = server + "/auth/realms/" + realm + "/protocol/openid-connect/auth"

    par = { 
    "redirect_uri" : "connector://authenticated",
    "response_type" : "code",
    "scope" : "openid",
    "client_id" : client_id,
    "nonce" : nonce 
    }
    
    res = requests.get(url, par)

    if res.status_code == 200:
        print("challange: ")
        challenge = res.headers['X-Auth-Challenge']
        location = res.headers['Location']
    else:
        print("nope: " + str(res.status_code) + "  " + res.content.decode("UTF-8"))
        sys.exit()

    return challenge, location





###############################
# schritt 3  -> signieren mit smcb
# finde smcbs

def getSDS(): 
    url = connectorURL + "/connector.sds"
    res = get(url, verify=False, pkcs12_filename=pkcs12_filename, pkcs12_password=pkcs12_password)
    if res.status_code == 200:
        print("sds:  ")
        root = getXMLRoot(res.content)  
        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
    else:
        print("nope: " + str(res.status_code) + "  " + res.status_code.decode("UTF-8"))
        sys.exit()

    return root

def getLocation(sds, name, tls): 
    #print(sds.findall('ServiceInformation/Service'))
    for service in sds.findall('ServiceInformation/Service'):
        #print(service.get('Name'))
        if service.get('Name') == name:
            xmlstr = minidom.parseString(ET.tostring(service)).toprettyxml(indent="   ")
            #print(xmlstr)
            if tls == True:
                endpoint = service.findall('Versions/Version/EndpointTLS')
            else:
                endpoint = service.findall('Versions/Version/Endpoint')
            #print(endpoint)
            return endpoint[0].get('Location')

def pretty(value, htchar='\t', lfchar='\n', indent=0):
    nlch = lfchar + htchar * (indent + 1)
    if type(value) is dict:
        items = [
            nlch + repr(key) + ': ' + pretty(value[key], htchar, lfchar, indent + 1)
            for key in value
        ]
        return '{%s}' % (','.join(items) + lfchar + htchar * indent)
    elif type(value) is list:
        items = [
            nlch + pretty(item, htchar, lfchar, indent + 1)
            for item in value
        ]
        return '[%s]' % (','.join(items) + lfchar + htchar * indent)
    elif type(value) is tuple:
        items = [
            nlch + pretty(item, htchar, lfchar, indent + 1)
            for item in value
        ]
        return '(%s)' % (','.join(items) + lfchar + htchar * indent)
    else:
        return repr(value)

def getXMLRoot(content):
    xml = content.decode("utf-8")

    # root = ET.fromstring(xml
    it = ET.iterparse(StringIO(xml))
    for _, el in it:
        prefix, has_namespace, postfix = el.tag.partition('}')
        if has_namespace:
            el.tag = postfix  # strip all namespaces
    root = it.root

    return root

def getNamespace(element):
    m = re.match('\{.*\}', element.tag)
    return m.group(0) if m else ''

def getCardHandleSMCB(sds):
    
    url = getLocation(sds, "EventService", connectorTLS)

    headers = {
    "Content-Type" : "text/xml; charset=utf-8",
    "SOAPAction" : "http://ws.gematik.de/conn/EventService/v7.2#GetCards", 
    "User-Agent" : "wsdl2objc",
    }

    body = """<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ZSTI_EventService="http://ws.gematik.de/conn/EventService/WSDL/v7.2" xmlns:ZSTI_EVT="http://ws.gematik.de/conn/EventService/v7.2" xmlns:ZSTI_CONN="http://ws.gematik.de/conn/ConnectorCommon/v5.0" xmlns:ZSTI_GERROR="http://ws.gematik.de/tel/error/v2.0" xmlns:dss="urn:oasis:names:tc:dss:1.0:core:schema" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:saml="urn:oasis:names:tc:SAML:1.0:assertion" xmlns:ZSTI_CCTX="http://ws.gematik.de/conn/ConnectorContext/v2.0" xmlns:ZSTI_CARD="http://ws.gematik.de/conn/CardService/v8.1" xmlns:ZSTI_CARDCMN="http://ws.gematik.de/conn/CardServiceCommon/v2.0" xmlns:ZSTI_PI="http://ws.gematik.de/int/version/ProductInformation/v1.1" xmlns:ZSTI_CTI="http://ws.gematik.de/conn/CardTerminalInfo/v8.0" xmlns:ZSTI_HSM="http://ws.gematik.de/conn/HsmInfo/v8.0" xsl:version="1.0">
      <soap:Body>
        <ZSTI_EVT:GetCards mandant-wide="true">
          <ZSTI_CCTX:Context>
            <ZSTI_CONN:MandantId>""" + mandant + """</ZSTI_CONN:MandantId>
            <ZSTI_CONN:ClientSystemId>""" + client + """</ZSTI_CONN:ClientSystemId>
            <ZSTI_CONN:WorkplaceId>""" + workplace + """</ZSTI_CONN:WorkplaceId>
          </ZSTI_CCTX:Context>
        </ZSTI_EVT:GetCards>
      </soap:Body>
    </soap:Envelope>"""

    res = post(url, data=body, headers=headers, verify=False, pkcs12_filename=pkcs12_filename, pkcs12_password=pkcs12_password)
    root = getXMLRoot(res.content)
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

    if res.status_code == 200:
        print("cards: ")
    else:
        print("nope: " + str(res.status_code) + "  " + xmlstr)
        sys.exit()



    for card in root.findall('Body/GetCardsResponse/Cards/Card'):
        #print(card)
        #print(card.findall('CardType'))
        ch = card.findall('CardHandle')[0].text
        ct = card.findall('CardType')[0].text
        iccsn = card.findall('Iccsn')[0].text
        ctid = card.findall('CtId')[0].text
        if ct == "SMC-B":
            print(ct + " : " +ctid)
            return ch

def getJobNumber(sds):

    url = getLocation(sds, "SignatureService", connectorTLS)

    headers = {
    "Content-Type" : "text/xml; charset=utf-8",
    "SOAPAction" : "http://ws.gematik.de/conn/SignatureService/v7.4#GetJobNumber", 
    "User-Agent" : "wsdl2objc",
    }

    body = """<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ZSTI_SignatureService="http://ws.gematik.de/conn/SignatureService/WSDL/v7.4" xmlns:ZSTI_SIG="http://ws.gematik.de/conn/SignatureService/v7.4" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:sp="urn:oasis:names:tc:dss-x:1.0:profiles:SignaturePolicy:schema#" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" xmlns:dss="urn:oasis:names:tc:dss:1.0:core:schema" xmlns:saml="urn:oasis:names:tc:SAML:1.0:assertion" xmlns:vr="urn:oasis:names:tc:dss-x:1.0:profiles:verificationreport:schema#" xmlns:tsl="http://uri.etsi.org/02231/v2#" xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion" xmlns:xenc="http://www.w3.org/2001/04/xmlenc#" xmlns:ZSTI_CERTCMN="http://ws.gematik.de/conn/CertificateServiceCommon/v2.0" xmlns:ZSTI_CONN="http://ws.gematik.de/conn/ConnectorCommon/v5.0" xmlns:ZSTI_GERROR="http://ws.gematik.de/tel/error/v2.0" xmlns:ZSTI_CCTX="http://ws.gematik.de/conn/ConnectorContext/v2.0" xsl:version="1.0">
      <soap:Body>
        <ZSTI_SIG:GetJobNumber>
          <ZSTI_CCTX:Context>
            <ZSTI_CONN:MandantId>""" + mandant + """</ZSTI_CONN:MandantId>
            <ZSTI_CONN:ClientSystemId>""" + client + """</ZSTI_CONN:ClientSystemId>
            <ZSTI_CONN:WorkplaceId>""" + workplace + """</ZSTI_CONN:WorkplaceId>
            <ZSTI_CONN:UserId>""" + user + """</ZSTI_CONN:UserId>
          </ZSTI_CCTX:Context>
        </ZSTI_SIG:GetJobNumber>
      </soap:Body>
    </soap:Envelope>"""

    res = post(url, data=body, headers=headers, verify=False, pkcs12_filename=pkcs12_filename, pkcs12_password=pkcs12_password)
    root = getXMLRoot(res.content)
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

    if res.status_code == 200:
        print("jobNumber: ")
    else:
        print("nope: " + str(res.status_code) + "  " + xmlstr)
        sys.exit()

    return root.findall('Body/GetJobNumberResponse/JobNumber')[0].text

def signData(sds, cardHandle, jobNumber, content):

   
    print("challenge: " + content)
    sha256_content = hashlib.sha256(content.encode()).hexdigest()
    print("sha.256:   " + sha256_content)
    content_bytes = sha256_content.encode('ascii')
    base64_bytes = base64.b64encode(content_bytes)
    base64_content = base64_bytes.decode('ascii')
    print("base64:    " + base64_content)

    url = getLocation(sds, "SignatureService", connectorTLS)

    headers = {
    "Content-Type" : "text/xml; charset=utf-8",
    "SOAPAction" : "http://ws.gematik.de/conn/SignatureService/v7.4#SignDocument", 
    "User-Agent" : "wsdl2objc",
    }

    body = """<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ZSTI_SignatureService="http://ws.gematik.de/conn/SignatureService/WSDL/v7.4" xmlns:ZSTI_SIG="http://ws.gematik.de/conn/SignatureService/v7.4" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:sp="urn:oasis:names:tc:dss-x:1.0:profiles:SignaturePolicy:schema#" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" xmlns:dss="urn:oasis:names:tc:dss:1.0:core:schema" xmlns:saml="urn:oasis:names:tc:SAML:1.0:assertion" xmlns:vr="urn:oasis:names:tc:dss-x:1.0:profiles:verificationreport:schema#" xmlns:tsl="http://uri.etsi.org/02231/v2#" xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion" xmlns:xenc="http://www.w3.org/2001/04/xmlenc#" xmlns:ZSTI_CERTCMN="http://ws.gematik.de/conn/CertificateServiceCommon/v2.0" xmlns:ZSTI_CONN="http://ws.gematik.de/conn/ConnectorCommon/v5.0" xmlns:ZSTI_GERROR="http://ws.gematik.de/tel/error/v2.0" xmlns:ZSTI_CCTX="http://ws.gematik.de/conn/ConnectorContext/v2.0" xsl:version="1.0">
      <soap:Body>
        <ZSTI_SIG:SignDocument>
          <ZSTI_CONN:CardHandle>""" + cardHandle + """</ZSTI_CONN:CardHandle>
          <ZSTI_CCTX:Context>
            <ZSTI_CONN:MandantId>""" + mandant + """</ZSTI_CONN:MandantId>
            <ZSTI_CONN:ClientSystemId>""" + client + """</ZSTI_CONN:ClientSystemId>
            <ZSTI_CONN:WorkplaceId>""" + workplace + """</ZSTI_CONN:WorkplaceId>
            <ZSTI_CONN:UserId>""" + user + """</ZSTI_CONN:UserId>
          </ZSTI_CCTX:Context>
          <ZSTI_SIG:TvMode>NONE</ZSTI_SIG:TvMode>
          <ZSTI_SIG:JobNumber>""" + jobNumber + """</ZSTI_SIG:JobNumber>
          <ZSTI_SIG:SignRequest RequestID=""" + '"' +  jobNumber + '"' + """>
            <ZSTI_SIG:OptionalInputs>
              <dss:SignatureType>urn:ietf:rfc:5652</dss:SignatureType>
            </ZSTI_SIG:OptionalInputs>
            <ZSTI_SIG:Document ID="ImpfZert">
              <dss:Base64Data MimeType="text/plain">""" + base64_content + """</dss:Base64Data>
            </ZSTI_SIG:Document>
            <ZSTI_SIG:IncludeRevocationInfo>false</ZSTI_SIG:IncludeRevocationInfo>
          </ZSTI_SIG:SignRequest>
        </ZSTI_SIG:SignDocument>
      </soap:Body>
    </soap:Envelope>"""

    res = post(url, data=body, headers=headers, verify=False, pkcs12_filename=pkcs12_filename, pkcs12_password=pkcs12_password)
    root = getXMLRoot(res.content)
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

    if res.status_code == 200:
        print("signedChallenge: ")
    else:
        print("nope: " + str(res.status_code) + "  " + xmlstr)
        sys.exit()

    return root.findall('Body/SignDocumentResponse/SignResponse/SignatureObject/Base64Signature')[0].text

def externalAuth(sds, cardHandle, content):

   
    #print("challenge: " + content)
    #sha256_content = hashlib.sha256(content.encode()).hexdigest()
    #print("sha256:    " + sha256_content)
    #content_bytes = sha256_content.encode('ascii')
    #base64_bytes = base64.b64encode(content_bytes)
    #base64_content = base64_bytes.decode('ascii')
    #print("base64:    " + base64_content)

    content_bytes = content.encode()
    sha265_hashobj = hashlib.sha256(content_bytes)
    sha265_bytes = bytearray(sha265_hashobj.digest())
    base64_bytes = base64.b64encode(sha265_bytes)
    base64_content = base64_bytes.decode('ascii')

    url = getLocation(sds, "AuthSignatureService", True)

    headers = {
    "Content-Type" : "text/xml; charset=utf-8",
    "SOAPAction" : "http://ws.gematik.de/conn/AuthSignatureService/v7.4#ExternalAuthenticate", 
    "User-Agent" : "wsdl2objc",
    }

    body = """<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ZSTI_AuthSignatureService="http://ws.gematik.de/conn/AuthSignatureService/WSDL/v7.4" xmlns:ZSTI_SIG="http://ws.gematik.de/conn/SignatureService/v7.4" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:sp="urn:oasis:names:tc:dss-x:1.0:profiles:SignaturePolicy:schema#" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" xmlns:dss="urn:oasis:names:tc:dss:1.0:core:schema" xmlns:saml="urn:oasis:names:tc:SAML:1.0:assertion" xmlns:vr="urn:oasis:names:tc:dss-x:1.0:profiles:verificationreport:schema#" xmlns:tsl="http://uri.etsi.org/02231/v2#" xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion" xmlns:xenc="http://www.w3.org/2001/04/xmlenc#" xmlns:ZSTI_CERTCMN="http://ws.gematik.de/conn/CertificateServiceCommon/v2.0" xmlns:ZSTI_CONN="http://ws.gematik.de/conn/ConnectorCommon/v5.0" xmlns:ZSTI_GERROR="http://ws.gematik.de/tel/error/v2.0" xmlns:ZSTI_CCTX="http://ws.gematik.de/conn/ConnectorContext/v2.0" xsl:version="1.0">
      <soap:Body>
        <ZSTI_SIG:ExternalAuthenticate>
          <ZSTI_CONN:CardHandle>""" + cardHandle + """</ZSTI_CONN:CardHandle>
          <ZSTI_CCTX:Context>
            <ZSTI_CONN:MandantId>""" + mandant + """</ZSTI_CONN:MandantId>
            <ZSTI_CONN:ClientSystemId>""" + client + """</ZSTI_CONN:ClientSystemId>
            <ZSTI_CONN:WorkplaceId>""" + workplace + """</ZSTI_CONN:WorkplaceId>
          </ZSTI_CCTX:Context>
          <ZSTI_SIG:OptionalInputs>
            <dss:SignatureType>urn:ietf:rfc:3447</dss:SignatureType>
            <ZSTI_SIG:SignatureSchemes>RSASSA-PSS</ZSTI_SIG:SignatureSchemes>
          </ZSTI_SIG:OptionalInputs>
          <ZSTI_SIG:BinaryString>
            <dss:Base64Data MimeType="application/octet-stream">""" + base64_content + """</dss:Base64Data>
          </ZSTI_SIG:BinaryString>
        </ZSTI_SIG:ExternalAuthenticate>
      </soap:Body>
    </soap:Envelope>"""

    #print(body)

    res = post(url, data=body, headers=headers, verify=False, pkcs12_filename=pkcs12_filename, pkcs12_password=pkcs12_password)
    root = getXMLRoot(res.content)
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

    if res.status_code == 200:
        print("signedChallenge: ")
    else:
        print("nope: " + str(res.status_code) + "  " + xmlstr)
        sys.exit()

    return root.findall('Body/ExternalAuthenticateResponse/SignatureObject/Base64Signature')[0].text

def getCertificate(sds, cardHandle):

    url = getLocation(sds, "CertificateService", connectorTLS)

    headers = {
    "Content-Type" : "text/xml; charset=utf-8",
    "SOAPAction" : "http://ws.gematik.de/conn/CertificateService/v6.0#ReadCardCertificate", 
    "User-Agent" : "wsdl2objc",
    }

    body = """<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:ZSTI_CertificateService="http://ws.gematik.de/conn/CertificateService/WSDL/v6.0" xmlns:ZSTI_CERT="http://ws.gematik.de/conn/CertificateService/v6.0" xmlns:ZSTI_GERROR="http://ws.gematik.de/tel/error/v2.0" xmlns:ZSTI_CONN="http://ws.gematik.de/conn/ConnectorCommon/v5.0" xmlns:dss="urn:oasis:names:tc:dss:1.0:core:schema" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:saml="urn:oasis:names:tc:SAML:1.0:assertion" xmlns:ZSTI_CERTCMN="http://ws.gematik.de/conn/CertificateServiceCommon/v2.0" xmlns:ZSTI_CCTX="http://ws.gematik.de/conn/ConnectorContext/v2.0" xsl:version="1.0">
      <soap:Body>
        <ZSTI_CERT:ReadCardCertificate>
          <ZSTI_CONN:CardHandle>""" + cardHandle + """</ZSTI_CONN:CardHandle>
          <ZSTI_CCTX:Context>
            <ZSTI_CONN:MandantId>""" + mandant + """</ZSTI_CONN:MandantId>
            <ZSTI_CONN:ClientSystemId>""" + client + """</ZSTI_CONN:ClientSystemId>
            <ZSTI_CONN:WorkplaceId>""" + workplace + """</ZSTI_CONN:WorkplaceId>
          </ZSTI_CCTX:Context>
          <ZSTI_CERT:CertRefList>
            <ZSTI_CERT:CertRef>C.AUT</ZSTI_CERT:CertRef>
          </ZSTI_CERT:CertRefList>
          <ZSTI_CERT:Crypt>RSA</ZSTI_CERT:Crypt>
        </ZSTI_CERT:ReadCardCertificate>
      </soap:Body>
    </soap:Envelope>"""

    res = post(url, data=body, headers=headers, verify=False, pkcs12_filename=pkcs12_filename, pkcs12_password=pkcs12_password)
    root = getXMLRoot(res.content)
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")

    if res.status_code == 200:
        print("certificate: ", xmlstr)
    else:
        print("nope: " + str(res.status_code) + "  " + xmlstr)
        sys.exit()

    return root.findall('Body/ReadCardCertificateResponse/X509DataInfoList/X509DataInfo/X509Data/X509Certificate')[0].text
    





###############################
# schritt 4 -> Submit Signed challenge and SMCB public certificate
# leider ist mit dem redirekt ein problem, da in der url ein connector:// steht und die 
# bibliothek versucht das ding aufzulösen => curl

def submitSignedChallengeOS(location, signedChallenge, certificate):

    command = """curl -is --request GET '""" + location + """' \
    --header 'x-auth-signed-challenge: """ + signedChallenge + """' \
    --header 'x-auth-certificate: """ + certificate + """' \
    """
    #os.system(command)


    with Popen(command, stdout=PIPE, stderr=None, shell=True) as process:
        output = process.communicate()[0].decode("utf-8")
        #print(output)

        for line in output.split("\n"):
            if 'location: ' in line:
                location = line.removeprefix('location:').strip()
                #print('jup:  ' + line) 

    return location

def submitSignedChallenge(location, signedChallenge, certificate):

    parsed = parse.urlparse(location)
    par = parse.parse_qs(parsed.query)
   
    url = parsed.scheme + "://" + parsed.netloc + parsed.path

   

    headers = {
    "x-auth-signed-challenge" : signedChallenge,
    "x-auth-certificate" : certificate,
    }

    #print(headers)

    res = requests.get(url, par, headers=headers)
    if res.status_code == 200:
        print("submitSignedChallenge:")
    elif res.status_code == 302:
        print("submitSignedChallenge:  => BINGO")
    else:
        print("nope: " + res.content.decode("utf-8"))
        sys.exit()





###############################
# schritt 5 -> token exchange

def tokenExchange(location):
    parsed = parse.urlparse(location)
    par = parse.parse_qs(parsed.query)
    #print(par)

    url = server + "/auth/realms/" + realm + "/protocol/openid-connect/token"

    par = { 
    "grant_type" : "authorization_code",
    "redirect_uri" : "connector://authenticated",
    "client_id" : client_id,
    "session_state" : par['session_state'],
    "code" : par['code']
    }

    headers = {
    "Content-Type" : "application/x-www-form-urlencoded"
    }
    
    res = requests.post(url, par, headers=headers)

    if res.status_code == 200:
        print("exchange token: " )
    else:
        print("nope: " + str(res.status_code) + "  " + res.content.decode("UTF-8"))
        sys.exit

    return res.content.decode("UTF-8")




###############################
# schritt 6 -> pdf erzeugen

def getpdf(token):
    url = issuer


    data = ast.literal_eval(token)
    

    headers = { 
    "Authorization" : "Bearer " + data['access_token'],
    "Accept": "application/pdf", # es geht noch  application/cbor+base45  und  application/cbor
    "Content-Type": "application/vnd.dgc.v1+json",
    }
   

    bodyZert = {
    "ver": "1.0.0",
    "nam": { 
        "fn": "Mustermann", 
        "gn": "Max"
        },
    "dob": "1979-04-14",
    "v": [{
        "id": "011111100",
        "tg": "840539006",
        "vp": "1119305005",
        "mp": "EU/1/20/1528",
        "ma": "ORG-100030215",
        "dn": 2,
        "sd": 2,
        "dt": "2021-04-14",
        "co": "NL",
        "is": "Ministry of Public Health, Welfare and Sport",
        "ci": "urn:uvci:01:NL:PlA8UWS60Z4RZXVALl6GAZ"
        }],
    }


    bodyGenesen = {
    "ver": "1.0.0",
    "nam": { 
        "fn": "Mustermann", 
        "gn": "Max"
        },
    "dob": "1979-04-14",
    "r": [{
    	"tg":"840539006",
    	"fr":"2021-06-21",
    	"df":"2021-06-21",
    	"du":"2021-12-18",
    	"id":"935304499"}],
    }


   
    
    print ("======================")
    if genesenZert==True:
        res = requests.post(url, json=bodyGenesen, headers=headers)
    else:
        res = requests.post(url, json=bodyZert, headers=headers)

    if res.status_code == 200:
        print("issue: " )
    else:
        print("nope: " + str(res.status_code) + "  " + res.content.decode("UTF-8"))
        sys.exit()

   
    pdfFile = open("filename.pdf", "wb")
    byteArray = bytearray(res.content)
    pdfFile.write(byteArray)











###############################
#### hier gehts los ###########
###############################
print("###############################")
sds = getSDS()
cardHandle = getCardHandleSMCB(sds)


nonce = ''.join([random.choice(string.digits) for _ in range(30)])
print(nonce)
challenge, location = getChallenge(nonce)
print(challenge)


signedChallenge = externalAuth(sds, cardHandle, challenge)
print(signedChallenge)

certificate = getCertificate(sds, cardHandle)
print(certificate)


authCode = submitSignedChallengeOS(location, signedChallenge, certificate)
print(authCode)



token = tokenExchange(authCode)
print(token)

getpdf(token)
