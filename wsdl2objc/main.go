package main

import (
	"encoding/xml"
	"fmt"
	"github.com/davecgh/go-spew/spew"
	"io/ioutil"
	_ "math"
	"os"
	_ "sort"
	_ "strconv"
	_ "strings"
)

func main() {
	var file string
	if len(os.Args) < 2 {
		file = "/Users/mth/Documents/zollsoft/TI-Infrastruktur/OPB1_Schemadateien_R164/conn/EventService.wsdl"
		fmt.Println("Usage : " + os.Args[0] + " file_name")
		//os.Exit(1)
	} else {
		file = os.Args[1]
	}

	xmlFile, err := os.Open(file)
	if err != nil {
		fmt.Println("Error opening file:", err)
		return
	}
	defer xmlFile.Close()
	fmt.Println("Successfully Opened " + file)

	// read our opened xmlFile as a byte array.
	byteValue, _ := ioutil.ReadAll(xmlFile)

	// we initialize our Users array
	var wsdl XMLwsdl
	// we unmarshal our byteArray which contains our
	// xmlFiles content into 'users' which we defined above
	xml.Unmarshal(byteValue, &wsdl)
	wsdl.updateRelations()

	spew.Dump(wsdl.Service)
}
