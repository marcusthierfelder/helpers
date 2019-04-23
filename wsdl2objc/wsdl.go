package main

import (
	"encoding/xml"
	_ "fmt"
)

/* https://www.predic8.de/wsdl-lernen.htm */

type XMLwsdl struct {
	XMLName xml.Name `xml:"definitions"`

	Types     XMLtypes      `xml:"types"`
	Messages  []XMLmessage  `xml:"message"`
	PortTypes []XMLportType `xml:"portType"`
	Bindings  []XMLbinding  `xml:"binding"`
	Service   XMLservice    `xml:"service"`
}

func (wsdl XMLwsdl) updateRelations() {

	for _, p := range wsdl.Service.Ports {
		p.updateBinding(wsdl)
	}

	for _, b := range wsdl.Bindings {
		b.updatePortType(wsdl)
	}
}

/* types */

type XMLtypes struct {
	Name string `xml:"name,attr"`
}

/* messagae */

type XMLmessage struct {
	Name  string          `xml:"name,attr"`
	Parts XMLmessage_part `xml:"part"`
}

type XMLmessage_part struct {
	Name    string `xml:"name,attr"`
	Element string `xml:"element,attr"`
}

/* portType */

type XMLportType struct {
	Name       string         `xml:"name,attr"`
	Operations []XMLoperation `xml:"operation"`
}

type XMLoperation struct {
	Name       string           `xml:"name,attr"`
	SoapAction XMLsoapOperation `xml:"operation"`
	input      XMLinput         `xml:"input"`
	outputs    []XMLoutput      `xml:"output"`
	faults     []XMLfault       `xml:"fault"`
}

type XMLsoapOperation struct {
	SoapAction string `xml:"soapAction,attr"`
}

type XMLinput struct {
	Name    string `xml:"name,attr"`
	Message string `xml:"message,attr"`
}

type XMLoutput struct {
	Name    string `xml:"name,attr"`
	Message string `xml:"message,attr"`
}

type XMLfault struct {
	Name    string `xml:"name,attr"`
	Message string `xml:"message,attr"`
}

/* binding */

type XMLbinding struct {
	Name            string `xml:"name,attr"`
	XMLportTypeName string `xml:"type,attr"`
	PortType        XMLportType
	SoapBinding     XMLsoapBinding `xml:"binding"`
	Operations      []XMLoperation `xml:"operation"`
}

func (b XMLbinding) updatePortType(wsdl XMLwsdl) {

}

type XMLsoapBinding struct {
	Style     string `xml:"style,attr"`
	Transport string `xml:"transport,attr"`
}

/* service */

type XMLservice struct {
	//XMLName xml.Name `xml:"service"`
	Name  string    `xml:"name,attr"`
	Ports []XMLport `xml:"port"`
}

type XMLport struct {
	//XMLName xml.Name `xml:"port"`
	Name           string `xml:"name,attr"`
	XMLbindingName string `xml:"binding,attr"`
	Binding        *XMLbinding
	Address        XMLaddress `xml:"address"`
}

func (p XMLport) updateBinding(wsdl XMLwsdl) {
	for _, b := range wsdl.Bindings {
		if b.Name == p.XMLbindingName {
			p.Binding = &b
		}
	}
}

type XMLaddress struct {
	Location string `xml:"location,attr"`
}
