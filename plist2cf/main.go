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
	VarName string
	
	Page int `plist:"page"`
	BackgroundImage string `plist:"backgroundImage"`
	Cfes []PlistCFE `plist:"customFormularElemente"`
}

type PlistCFE struct {
	VarName string
	
	FeldName string `plist:"feldName"`
	Font string `plist:"font"`
	Fontsize int `plist:"fontSize"`
	Format string `plist:"format"`
	Height float32 `plist:"height"`
	Listenpos int `plist:"listenpos"`
	Modus int `plist:"modus"`
	ShowInKarteitext int `plist:"showInKarteitext"`
	Visible int `plist:"visible"`
	Width float32 `plist:"width"`
	Xpos float32 `plist:"xpos"`
	Ypos float32 `plist:"ypos"`
}

func (cfp PlistCFP) BackgroundImageFormated() string {

	str := cfp.BackgroundImage;

	reg, err := regexp.Compile(`\r?\n`)
	if err != nil {
    	log.Fatal(err)
	}	
	str = reg.ReplaceAllString(str, "\\n\" \n + \"");
	
	return str;
}

func (cf PlistCF) CustomImageFormated() string {

	str := cf.CustomImage;

	reg, err := regexp.Compile(`\r?\n`)
	if err != nil {
    	log.Fatal(err)
	}	
	str = reg.ReplaceAllString(str, "\\n\" \n + \"");
	
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

func (cfe PlistCFE) FormatFormated() string {
	str := cfe.Format
	reg, err := regexp.Compile(`"`)
	if err != nil {
    	log.Fatal(err)
	}
	str = reg.ReplaceAllString(str, "\\\"");

	reg, err = regexp.Compile(`\r?\n`)
	if err != nil {
    	log.Fatal(err)
	}	
	str = reg.ReplaceAllString(str, "\\n\" \n + \"");

	return str;
}



/**/
type ByListenpos []PlistCFE
func (a ByListenpos) Len() int           { return len(a) }
func (a ByListenpos) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByListenpos) Less(i, j int) bool { return a[i].Listenpos < a[j].Listenpos }


const tmplPattern = 
`{{template "formular" .}}`

const tmplFormular = 
`{{define "formular" -}}
Formulartyp {{$.VarName}} = findUniqueOrFirstVisible("{{.Name}}");
if ({{$.VarName}} == null) {
	{{$.VarName}} = createCustomFormular("{{.Kuerzel}}", "{{.Name}}", "{{.Tooltip}}", {{.Art}}, "{{.Font}}", {{.Fontsize}}, {{.NumberOfDirectPages}}, {{if .OhneArztStempel}}true{{else}}false{{end}}, {{.Papersize_height}}, {{.Papersize_width}}, "{{.Xibfile}}");	
	CustomFormularPage cfp;
	{{range $index, $page := $.Cfps -}} 
		{{template "page" . }}  
	{{end}}
	{{if ne (len .CustomImageFormated) 0}}{{$.VarName}}.setCustomImage("{{.CustomImageFormated}}");{{end}}
}
{{end}}`

const tmplPage = 
`{{define "page" -}} 
	cfp = createCustomFormularPage({{.Page}});
	{{if ne (len .BackgroundImageFormated) 0}}cfp.setBackgroundImage("{{.BackgroundImageFormated}}");{{end}}
	{{range .Cfes -}} 
		{{template "element" . }}  
	{{end}}
	{{- .VarName}}.addCustomFormularPages(cfp);
{{- end}}`

const tmplElement = 
`{{define "element" -}} 
	cfp.addCustomFormularElemente(createCustomFormularElement("{{.FeldName}}", "{{.Font}}", {{.Fontsize}}, "{{.FormatFormated}}", {{.Height}}, {{.Listenpos}},{{.Modus}}, {{if .ShowInKarteitext}}true{{else}}false{{end}},{{.Width}},{{.Xpos}},{{.Ypos}}));
{{- end}}`







/*****************************************************
los geht

*/
func main() {

	if len(os.Args) < 2 {
		fmt.Println("Usage : " + os.Args[0] + " file_name")
		os.Exit(1)
	}

	result := ""
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
    	for i, _ := range data.Cfps {
			data.Cfps[i].VarName = data.VarName

			tmp := data.Cfps[i].Cfes[:0]
			for j, cfe := range data.Cfps[i].Cfes {
				if (data.Cfps[i].Cfes[j].Visible == 1) {
					tmp = append(tmp, cfe)
				}
			}
			data.Cfps[i].Cfes = tmp

			for j, _ := range data.Cfps[i].Cfes {
				data.Cfps[i].Cfes[j].VarName = data.VarName
			}
		}


		// sortieren nach den pages und listenpositionen
		sort.Slice(data.Cfps, func(i, j int) bool {
	  		return data.Cfps[i].Page < data.Cfps[j].Page
		})
		for _, page := range data.Cfps {
			sort.Slice(page.Cfes[:], func(i, j int) bool {
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

		result = result + "\n\n" + tpl.String()
	}


	fmt.Println(""+result);
	clipboard.WriteAll(result);

	
}
















