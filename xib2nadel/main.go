package main

import (
	"encoding/xml"
	"fmt"
	"math"
	"os"
	"sort"
	"strconv"
	"strings"
)

// tabviewitem
type XMLTabViewItem struct {
	Id         string  `xml:"id,attr"`
	Label      string  `xml:"label,attr"`
	UserLabel  string  `xml:"userLabel,attr"`
	Identifier string  `xml:"identifier,attr"`
	View       XMLView `xml:"view"`
}

// textFields
type XMLTextField struct {
	Id          string         `xml:"id,attr"`
	CustomClass string         `xml:"customClass,attr"`
	Rect        XMLRect        `xml:"rect"`
	Connections XMLConnections `xml:"connections"`
}

// textviews
type XMLScrollView struct {
	Id          string      `xml:"id,attr"`
	CustomClass string      `xml:"customClass,attr"`
	Rect        XMLRect     `xml:"rect"`
	ClipView    XMLClipView `xml:"clipView"`
}

type XMLClipView struct {
	SubViews XMLSubViews `xml:"subviews"`
}

type XMLSubViews struct {
	TextViews XMLTextView `xml:"textView"`
}
type XMLTextView struct {
	//Id         string        `xml:"id,attr"`
	Rect        XMLRect        `xml:"rect"`
	Connections XMLConnections `xml:"connections"`
}

// helper stuff
type XMLRect struct {
	X string `xml:"x,attr"`
	Y string `xml:"y,attr"`
	H string `xml:"height,attr"`
	W string `xml:"width,attr"`
}

type XMLConnections struct {
	BindingList []XMLBinding `xml:"binding"`
}

type XMLBinding struct {
	KeyPath string `xml:"keyPath,attr"`
	Name    string `xml:"name,attr"`
}

type XMLView struct {
	Rect       XMLRect `xml:"rect"`
	Identifier string  `xml:"identifier,attr"`
	Key        string  `xml:"key,attr"`
}

// container
type XIBAll struct {
	Pages []XIBPage
}

func (a *XIBAll) addPage(p XIBPage) {
	a.Pages = append(a.Pages, p)
}

func (a *XIBAll) addObj(o XIBObj) {
	p := &(a.Pages[len(a.Pages)-1])
	p.addObj(o)
}

func (a *XIBAll) sort() {
	for _, p := range a.Pages {
		p.sort()
	}
}

func (a *XIBAll) printNadel() {
	a.sort()
	for _, p := range a.Pages {
		p.printNadel()
	}
}

type XIBPage struct {
	W    int
	H    int
	Name string
	Objs XIBObjs
}

func (p *XIBPage) addObj(o XIBObj) {
	p.Objs = append(p.Objs, o)
}

func (p *XIBPage) sort() {
	// TODO:
	sort.Sort(XIBObjs(p.Objs))
}

func (p *XIBPage) printNadel() {
	if len(p.Objs) > 0 {
		fmt.Println("// --------- ")
		for _, o := range p.Objs {
			o.printNadel()
		}
	}
}

type XIBObj struct {
	X       int
	Y       int
	W       int
	H       int
	KeyPath string
}

func (o *XIBObj) printNadel() {
	xmax := 882.
	ymax := 1244.
	hline := 0.65

	x := (float64(o.X)) / xmax * 21.0
	y := (ymax - float64(o.Y)) / ymax * 29.7
	w := (float64(o.W)) / xmax * 21.0
	h := (float64(o.H)) / ymax * 29.7
	l := 1.

	if strings.Contains(o.KeyPath, ".textfield_") {
		l = math.Floor(h / hline)
		y -= (l - 1) * hline
	} else {
		x += .2
	}

	xstr := strconv.FormatFloat(x, 'f', 2, 64)
	ystr := strconv.FormatFloat(y, 'f', 2, 64)
	wstr := strconv.FormatFloat(w, 'f', 2, 64)
	hstr := strconv.FormatFloat(hline, 'f', 2, 64)
	lstr := strconv.FormatFloat(l, 'f', 0, 64)

	value := "[self.formular valueForKey:" + "@\"" + strings.Replace(o.KeyPath, "formular.", "", -1) + "\"" + "]"

	if strings.Contains(o.KeyPath, ".textfield_") {
		if strings.EqualFold(lstr, "1") {
			fmt.Println("[zsnd addLineAbsolute:" + value + " andPx:" + xstr + " andPy:" + ystr + " andFS:10 andLength:" + wstr + "];")
		} else {
			fmt.Println("[zsnd addLineAbsolute:" + value + " andPx:" + xstr + " andPy:" + ystr + " andFS:10 andLineHeigth:" + hstr + " andLength:" + wstr + " andMaxLines:" + lstr + "];")
		}
	} else {
		fmt.Println("[zsnd addLineAbsolute:" + value + " andPx:" + xstr + " andPy:" + ystr + " andFS:10];")
	}
}

// hilfcontrukt um den slice easy peacy sortieren zu können
type XIBObjs []XIBObj

func (slice XIBObjs) Len() int {
	return len(slice)
}

func (slice XIBObjs) Less(i, j int) bool {
	return slice[i].Y > slice[j].Y || (slice[i].Y == slice[j].Y && slice[i].X < slice[j].X)
}

func (slice XIBObjs) Swap(i, j int) {
	slice[i], slice[j] = slice[j], slice[i]
}

/*****************************************************
los geht

*/
func main() {

	if len(os.Args) < 2 {
		fmt.Println("Usage : " + os.Args[0] + " file_name")
		os.Exit(1)
	}

	file := os.Args[1]

	xmlFile, err := os.Open(file)
	if err != nil {
		fmt.Println("Error opening file:", err)
		return
	}
	defer xmlFile.Close()
	fmt.Println("Successfully Opened " + file)

	decoder := xml.NewDecoder(xmlFile)
	all := XIBAll{}

	for {
		t, _ := decoder.Token()
		if t == nil {
			break
		}
		switch se := t.(type) {
		case xml.StartElement:
			inElement := se.Name.Local

			if inElement == "tabViewItem" {
				fmt.Println(inElement)
				all.addPage(XIBPage{Name: ""})
			}

			if inElement == "textField" {
				var tf XMLTextField
				decoder.DecodeElement(&tf, &se)

				keyPath := ""
				for _, b := range tf.Connections.BindingList {
					if strings.Compare(b.Name, "value") == 0 {
						keyPath = b.KeyPath
					}
				}

				startsWith1 := strings.HasPrefix(keyPath, "formular.checkbox_")
				startsWith2 := strings.HasPrefix(keyPath, "formular.textfield_")

				if startsWith1 || startsWith2 {
					//fmt.Println("textField (" + tf.Id + ")  " + tf.Rect.X + " " + tf.Rect.Y + "  -> " + keyPath)
					xpos, _ := strconv.Atoi(tf.Rect.X)
					ypos, _ := strconv.Atoi(tf.Rect.Y)
					w, _ := strconv.Atoi(tf.Rect.W)
					h, _ := strconv.Atoi(tf.Rect.H)
					all.addObj(XIBObj{X: xpos, Y: ypos, W: w, H: h, KeyPath: keyPath})
				}

			}

			if inElement == "scrollView" {
				var sv XMLScrollView
				decoder.DecodeElement(&sv, &se)
				tv := sv.ClipView.SubViews.TextViews

				keyPath := ""
				for _, b := range tv.Connections.BindingList {
					if strings.Compare(b.Name, "value") == 0 {
						keyPath = b.KeyPath
					}
				}

				startsWith1 := strings.HasPrefix(keyPath, "formular.checkbox_")
				startsWith2 := strings.HasPrefix(keyPath, "formular.textfield_")

				if startsWith1 || startsWith2 {
					//fmt.Println("textView (" + sv.Id + ")  " + sv.Rect.X + " " + sv.Rect.Y + "  -> " + keyPath)
					xpos, _ := strconv.Atoi(sv.Rect.X)
					ypos, _ := strconv.Atoi(sv.Rect.Y)
					w, _ := strconv.Atoi(sv.Rect.W)
					h, _ := strconv.Atoi(sv.Rect.H)
					all.addObj(XIBObj{X: xpos, Y: ypos, W: w, H: h, KeyPath: keyPath})
				}

			}

		default:
		}
	}

	all.printNadel()
	//fmt.Println(all.Pages)
}
