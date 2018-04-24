package main

import (
	"fmt"
	"os"
	"howett.net/plist"
	"strings"
	"text/template"
	//"reflect"
	"sort"
	"log"
	"regexp"
)


type PlistCKE struct {
	VarName string
	Name string `plist:"name"`
	Kuerzel string `plist:"kuerzel"`
	Ckees []PlistCKEE `plist:"customKarteiEintragEntries"`
	Width int `plist:"popoverWidth"`
	Cols int `plist:"columnCount"`
}

type PlistCKEE struct {
	AnzeigeName string `plist:"anzeigeName"`
	Listenpos int `plist:"listenpos"`
	Modus string `plist:"modus"`
	Name string `plist:"name"`
	Removed int `plist:"removed"`
	ShowInKarteitext int `plist:"showInKarteitext"`
	Vorauswahl string `plist:"vorauswahl"`
	Auswahl string `plist:"auswahl"`
	WidthLabel int `plist:"widthLabel"`
	WidthValue int `plist:"widthValue"`
	ColumnCount int `plist:"columnCount"`
}

func (ckee *PlistCKEE) VorauswahlSpecial() string {

	reg, err := regexp.Compile(`\r?\n`)
	if err != nil {
    	log.Fatal(err)
	}
	
	return reg.ReplaceAllString(ckee.Vorauswahl, "\\n\" \n + \"");
}

const tmplPattern = `
KarteiEintragTyp {{.VarName}} = findUniqueOrFirstVisible("{{.Kuerzel}}");
if ({{.VarName}} == null) {
	{{.VarName}} = createCustomKarteiEintrag("{{.Kuerzel}}", "{{.Name}}", {{.Width}}, {{.Cols}});	{{$VarName := .VarName}}{{$Cols := .Cols}}  {{range .Ckees}}
	{{$VarName}}.addCustomKarteiEintragEntries(createCustomEntry("{{.Modus}}", {{.Listenpos}}, "{{.Name}}", "{{.AnzeigeName}}", "", "{{.VorauswahlSpecial}}", "{{.Auswahl}}", {{.WidthLabel}}, {{.WidthValue}}, {{$Cols}}, {{if .ShowInKarteitext}}true{{else}}false{{end}}));   {{end}}
}
`






/*****************************************************
los geht

*/
func main() {

	if len(os.Args) < 2 {
		fmt.Println("Usage : " + os.Args[0] + " file_name")
		os.Exit(1)
	}

	for iArg := 1; iArg < len(os.Args); iArg++ {

		file := os.Args[iArg]


		// file öffnen und schliessen
		buffer, err := os.Open(file)
		if err != nil {
			log.Fatal(err)
		}
		defer buffer.Close()
		//fmt.Println("Successfully Opened " + file)



		// einlesen der plist und mappen auf das struct-"model"
		var data PlistCKE
		decoder := plist.NewDecoder(buffer)
		err = decoder.Decode(&data)
		if err != nil {
		    log.Fatal(err)
		}
		
		// guter variablenname
		reg, err := regexp.Compile("[^a-zA-Z0-9]+")
    	if err != nil {
        	log.Fatal(err)
    	}
    	data.VarName = reg.ReplaceAllString(strings.ToLower(data.Kuerzel), "")


		// sortieren nach den listenpositionen
		sort.Slice(data.Ckees, func(i, j int) bool {
	  		return data.Ckees[i].Listenpos < data.Ckees[j].Listenpos
		})


		//create a new template with some name
		tmpl := template.Must(template.New("").Parse(tmplPattern))


		//merge template 'tmpl' with content of 's'
	    err = tmpl.Execute(os.Stdout, data)
	    if err  != nil {
	        log.Fatal(err)
	    }

	}
	
}
















