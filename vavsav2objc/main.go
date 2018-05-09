package main

import (
	"fmt"
	"os"
	_ "howett.net/plist"
	"strings"
	"text/template"
	//"reflect"
	_ "sort"
	"log"
	"regexp"
	 "github.com/atotto/clipboard"
	 "bytes"
	"bufio"
	"strconv"
	"math"
)


type Katalog struct {
	Parents []Parent
}

type Parent struct {
	Ziffer float64
	Text string
	
	Children []Child
}

type Child struct {
	Ziffer float64
	Text string
	VAV bool
}


func (p Parent) TextFormated() string {
	str := strings.Trim(p.Text, "\n")
	
	reg, err := regexp.Compile(`\r?\n`)
	if err != nil {
    	log.Fatal(err)
	}	
	str = reg.ReplaceAllString(str, "\\n\" \n \"");

	return str;
}

func (c Child) TextFormated() string {
	str := strings.Trim(c.Text, "\n")
	
	reg, err := regexp.Compile(`\r?\n`)
	if err != nil {
    	log.Fatal(err)
	}	
	str = reg.ReplaceAllString(str, "\\n\" \n \"");

	return str;
}





const tmplPattern = 
`{{range $index, $p := $.Parents -}} {{template "parent" $p }}  {{end}}`

const tmplParent = 
`{{define "parent" -}}
	dict = [self newElementForParent:ret ziffer:@({{.Ziffer}}) vav:nil text:@"{{.TextFormated}}"];
	{{range $index, $c := $.Children -}} {{template "child" $c }}  {{end}}
{{end}}`

const tmplChild = 
`{{define "child" -}} 
	[self newElementForParent:dict ziffer:@({{.Ziffer}}) vav:{{if .VAV}}@YES{{else}}@NO{{end}} text:@"{{.TextFormated}}"];
{{end}}`








/*****************************************************
los geht

*/
func main() {

	if len(os.Args) < 2 {
		fmt.Println("Usage : " + os.Args[0] + " file_name")
		os.Exit(1)
	}

	

	file := os.Args[1]

	// file öffnen und schliessen
	buffer, err := os.Open(file)
	if err != nil {
		log.Fatal(err)
	}
	defer buffer.Close()
	//fmt.Println("Successfully Opened " + file)


	var katalog Katalog
	var isParent bool


	scanner := bufio.NewScanner(buffer)
    for scanner.Scan() {
        //fmt.Println(scanner.Text())
        line := scanner.Text()


        f, err := strconv.ParseFloat(line, 64)
        if err == nil {
        	if f == math.Trunc(f) {
        		isParent = true
				//log.Println("parent " + line)
    			katalog.Parents = append(katalog.Parents, Parent{Ziffer: f})

    		} else {
    			isParent = false
    			//log.Println("child " + line)
    			p := &katalog.Parents[len(katalog.Parents)-1:][0]
				p.Children = append(p.Children, Child{Ziffer: f})

    		}

        } else {
			p := &katalog.Parents[len(katalog.Parents)-1:][0]
        	if (isParent) {
        		p.Text = line
        	} else {
        		c := &p.Children[len(p.Children)-1:][0]
        		if strings.Compare(line, "(V)") == 0 {
        			c.VAV = true
        		} else if strings.Compare(line, "(S)") == 0 {
        			c.VAV = false
        		} else {
        			c.Text = c.Text  + line  + "\n"
        		}
        	}

        }
    }

    if err := scanner.Err(); err != nil {
        log.Fatal(err)
    }



    //create a new template with some name
	tmpl := template.Must(template.New("").Parse(tmplPattern))
	tmpl = template.Must(tmpl.Parse(tmplParent));
	tmpl = template.Must(tmpl.Parse(tmplChild));
	

	
    var tpl bytes.Buffer
	err = tmpl.Execute(&tpl, katalog)
	if err != nil {
	    log.Fatal(err)
	}

	

    fmt.Println(""+tpl.String());
	clipboard.WriteAll(tpl.String());
	
}
















