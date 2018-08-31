import sys
import provconv
import prov

template=prov.model.ProvDocument.deserialize(sys.argv[1], format="rdf", rdf_format="xml")

bindings_dict=provconv.read_binding(sys.argv[2])
#print bindings_dict


exp=provconv.instantiate_template(template, bindings_dict)

outfilename=sys.argv[3]
toks=outfilename.split(".")
frmt=toks[len(toks)-1]
if frmt in ["rdf", "xml", "json", "ttl", "trig", "provn"]:
	outfile=open(outfilename, "w")
	if frmt in ["xml", "provn", "json"]:
		outfile.write(exp.serialize(format=frmt))
	else:	
		if frmt == "rdf":
			frmt="xml"
		outfile.write(exp.serialize(format="rdf", rdf_format=frmt))
	outfile.close()

