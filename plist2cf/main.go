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
	"github.com/atotto/clipboard"
	"bytes"
)


type PlistCF struct {
	VarName string
	
	Name string `plist:"name"`
	Kuerzel string `plist:"kuerzel"`
	Tooltip string `plist:"tooltip"`
	
	Art int `plist:"art"`
	CustomFormularDefaultTyp int `plist:"customFormularDefaultTyp"`
	CustomFormular int `plist:"customFormular"`
	CustomImage string `plist:"customImage"`
	DirectPrint int `plist:"directPrint"`
	Font string `plist:"font"`
	Fontsize float32 `plist:"fontsize"`
	InKarteiToolbar int `plist:"inKarteiToolbar"`
	InTageslisteToolbar int `plist:"inTageslisteToolbar"`
	NumberOfDirectPages int `plist:"numberOfDirectPages"`
	OhneArztStempel int `plist:"ohneArztStempel"`
	Papersize_height float32 `plist:"papersize_height"`
	Papersize_width float32 `plist:"papersize_width"`
	ShowElementBackground int `plist:"showElementBackground"`
	Version string `version"`
	Xibfile string `plist:"xibfile"`

	Cfps []PlistCFP `plist:"customFormularPages"`
	
}

type PlistCFP struct {
	Page int `plist:"page"`
	Cfes []PlistCFE `plist:"customFormularElemente"`
}

type PlistCFE struct {
	FeldName string `plist:"feldName"`
	Font string `plist:"font"`
	Format string `plist:"format"`
	Height float32 `plist:"height"`
	Listenpos int `plist:"listenpos"`
	Modus int `plist:"modus"`
	HowInKarteitext int `plist:"howInKarteitext"`
	Width float32 `plist:"width"`
	Xpos float32 `plist:"xpos"`
	Ypos float32 `plist:"ypos"`
}

func (cf PlistCF) CustomImageFormated() string {

	str := filterNewLines(cf.CustomImage);

	re := regexp.MustCompile(`.{200}`) // Every 5 chars
    parts := re.FindAllString(str, -1) // Split the string into 5 chars blocks.
    str = strings.Join(parts, "\" \n + \"") // Put the string back together
	
	return str;
}

func filterNewLines(s string) string {
    return strings.Map(func(r rune) rune {
        switch r {
        case 0x000A, 0x000B, 0x000C, 0x000D, 0x0085, 0x2028, 0x2029:
            return -1
        default:
            return r
        }
    }, s)
}




const tmplPattern = 
`{{template "formular" .}}`

const tmplFormular = 
`{{define "formular" -}}
Formulartyp {{$.VarName}} = findUniqueOrFirstVisible("{{.Name}}");
if ({{$.VarName}} == null) {
	{{$.VarName}} = createCustomFormular("{{.Kuerzel}}", "{{.Name}}", "{{.Tooltip}}", );	
	CustomFormularPage cfp;
	{{range $index, $page := $.Cfps -}} 
		{{template "page" . }}  
		{{- $.VarName}}.addCustomFormularPages(cfp);
	{{end}}
	{{$.VarName}}.setCustomImage("{{.CustomImageFormated}}");
}
{{end}}`

const tmplPage = 
`{{define "page" -}} 
	cfp = blabla({{.Page}});
	{{range .Cfes -}} 
		{{template "element" . }}  
	{{end}}
{{- end}}`

const tmplElement = 
`{{define "element" -}} 
	cfp.addCustomFormularElement("{{.FeldName}}", {{.Listenpos}})
{{- end}}`







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
		var data PlistCF
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
		for _, page := range data.Cfps {
			//fmt.Println("... " + page.Page)
			sort.Slice(page.Cfes, func(i, j int) bool {
		  		return page.Cfes[i].Listenpos < page.Cfes[j].Listenpos
			})
		}

		//create a new template with some name
		tmpl := template.Must(template.New("").Parse(tmplPattern))
		tmpl = template.Must(tmpl.Parse(tmplFormular));
		tmpl = template.Must(tmpl.Parse(tmplPage));
		tmpl = template.Must(tmpl.Parse(tmplElement));

		

		var tpl bytes.Buffer
		err = tmpl.Execute(&tpl, data)
		if err != nil {
		    log.Fatal(err)
		}

		result := tpl.String()
		fmt.Println("fertsch"+result);


	    clipboard.WriteAll(result);

	}
	
}
















