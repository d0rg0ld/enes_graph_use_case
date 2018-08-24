import openpyxl
import sys
import codecs
import dateutil.parser as parser
import dateutil.tz as tz
import pandas
import urllib
#import urllib.parse

sys.path.insert(0, '/home/goldfarb/envriProvenance/enes_graph_use_case/prov_templates/provtemplates')

import provconv
import prov.model as prov

filename="PNP_20180321.xlsx"

wb=openpyxl.load_workbook(filename)

data=wb["IP2-PNP_Vorseite"]


date=data["c6"].value

counter=7
persons=list()
run=True

while run:
        index="c"+str(counter)
        run=True
        try:
                if data[index].value!=None and data[index].value!="":
                        persons.append(data[index].value)
                else:
                        run=False
        except:
                run=False
                pass
        counter+=1

counter=6
trees=dict()
run=True
fnames=[data["n5"].value,data["o5"].value,data["p5"].value,data["q5"].value]
#fnames=[data["m5"].value, data["n5"].value,data["o5"].value,data["p5"].value,data["q5"].value]
def checkNone(data):
        if data==None:
                return ""
        else:
                return str(data).strip("() ")

            
while run:
        index="m"+str(counter)
        run=True
        try:
                if data[index].value!=None and data[index].value!="":
                        idx=checkNone(str(data[index].value))
                        trees[idx]=dict()
                        tree=trees[idx]
                        tree[fnames[0]]=checkNone(data["n"+str(counter)].value)
                        tree[fnames[1]]=checkNone(data["o"+str(counter)].value)
                        tree[fnames[2]]=checkNone(data["p"+str(counter)].value)
                        tree[fnames[3]]=checkNone(data["q"+str(counter)].value)
                        trees[idx]=tree
                else:
                        run=False
        except:
                run=False
                pass
        counter+=1
        
   

out=dict()
#for n in fnames:
#    output[n]=list()   
extracols=["date", "person","tree"]
cols=extracols+fnames
for col in cols:
    out[col]=[]
    for p in persons:
        for t in trees:
            if col not in extracols:
                try:
                    out[col].append(trees[t][col])
                except:
                    pass
            else:
                if col=="date":
                    out[col].append(str(date.isoformat()))
                if col=="person":
                    out[col].append(p)
                if col=="tree":
                    out[col].append(t)
  
#print(repr(out))
data=pandas.DataFrame(out)                    
print(data)

    #add manual stuff
    
#think about it another way
#create mapping
#colname varname value type



#manual mapping for colname-varname-type
bindmap={ "Anmerkung" : { "varname" : "comment", "type" : "attr", "val" : "literal"},
  "Dendrometer" : { "varname" : "dendrometer", "type" : "entity", "val" : "iri" },
  "[cm]" : { "varname" : "readValue", "type" : "attr", "val" : "numvalue"},
  "date" : { "varname" : "endDate", "type" : "attr", "val" : "literal" },
  "person" : { "varname" : "readingAgent", "type" : "entity", "val" : "iri" },
  "tree" : { "varname" : "tree", "type" : "entity", "val" : "iri" }
 }

template="""
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix tmpl: <http://openprovenance.org/tmpl#> .
@prefix var: <http://openprovenance.org/var#> .
@prefix ex: <http://example.com#> .

"""

outNSpref="ex"
outNS="http://example.com#"

bind_dicts=[]

for index, row in data.iterrows():
    rtemplate=template
    bind_dict={}
    for col in data.columns.values:
        if col in bindmap:

            outstatement="var:"+bindmap[col]["varname"] + " a prov:Entity ;\n"
	    #print repr(row)
            outval=str(row[col].encode('utf8', 'replace'))

            if bindmap[col]["val"]=="iri":
                outval=prov.QualifiedName(prov.Namespace(outNSpref,outNS), urllib.quote(outval))

	    #print col + " " + bindmap[col]["varname"] + " " + outval
            bind_dict["var:"+bindmap[col]["varname"]]=outval
            #outval=row[col]
            if bindmap[col]["val"]=="literal":
                outval='"'+outval+'"'

            if bindmap[col]["type"]=="attr":
                outstatement=outstatement + "\ttmpl:2dvalue_0_0 " + str(outval) + " .\n"
            else:
                outstatement=outstatement + "\ttmpl:value_0 " + str(outval) + " .\n"
            rtemplate=rtemplate+outstatement
            
    
    bind_dicts.append(bind_dict)

print(rtemplate)
    
    
provtemplate=prov.ProvDocument()    
res=provtemplate.deserialize(source="excelProvTemplate.rdf", format="rdf", rdf_format="xml")
print(bind_dicts[0])
print(res.serialize(format="rdf"))
exp=provconv.instantiate_template(res, bind_dicts[0])

print(exp.serialize(format="provn"))
