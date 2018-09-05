import sys
import provconv
import prov
import getopt
import json

def setEntry(rec, regNS):
	#keys:	@id	(for quali)

	#	@type	(for value)
	#	@value	(for value)
	out=rec
	# we got a qualified namea
	try:
		if "@id" in rec:
			toks=rec["@id"].split(":")
			if len(toks) > 2:
				print "Invalid Qualified Name " + rec["@id"] + " found in V3 Json Binding"
			for ns in regNS.get_registered_namespaces():
				if ns.prefix==toks[0]:
					out=prov.model.QualifiedName(ns, toks[1])	
		if "@value" in rec:
			if "@type" in rec:
				out=prov.model.Literal(rec["@value"], datatype=rec["@type"])	
			else:
				out=rec["@value"]
	except:
		print "Error parsing " + repr(rec)
		pass
	return out

#make more formats available
#template=prov.model.ProvDocument.deserialize(sys.argv[1], format="rdf", rdf_format="xml")
try:
	opts, args = getopt.getopt(sys.argv[1:], "hi:o:b:v3", ["help", "infile=", "outfile=", "bindings=", "verbose", "bindver3"])
except getopt.GetoptError as err:
	print str(err)  # will print something like "option -a not recognized"
	usage()
	sys.exit(2)

infile=None
outfile=None
bindings=None
verbose=False
v3=False

for o, a in opts:
	if o == "-v":
		verbose = True
	elif o in ("-h", "--help"):
		#usage()
		sys.exit()
	elif o in ("-o", "--outfile"):
		outfile = a
	elif o in ("-i", "--infile"):
		infile = a
	elif o in ("-b", "--bindings"):
		bindings = a
	elif o in ("-3", "--bindver3"):
		v3=True
	else:
		assert False, "unhandled option"

if not infile or not bindings:
	sys.exit()


template=prov.read(infile)

bindings_dict=None


if v3:
	bindings_dict=dict()
	v3_dict=json.load(open(bindings, "r"))
	if "context" in v3_dict:
		print v3_dict["context"]
		namespaces=set()
		for k in  v3_dict["context"]:
			namespaces.add(prov.model.Namespace(k, v3_dict["context"][k]))	
		template=provconv.set_namespaces(namespaces, template)
	if "var" in v3_dict:	
		for v in v3_dict["var"]:
			val=list()
			for rec in v3_dict["var"][v]:
				val.append(setEntry(rec, template._namespaces))
			bindings_dict["var:"+v]=val
	if "vargen" in v3_dict:	
		for v in v3_dict["vargen"]:
			val=list()
			for rec in v3_dict["vargen"][v]:
				val.append(setEntry(rec, template._namespaces))
			bindings_dict["vargen:"+v]=val
else:
	bindings_doc=prov.read(bindings)
	bindings_dict=provconv.read_binding(bindings_doc)
	print(bindings_doc.namespaces)
	template=provconv.set_namespaces(bindings_doc.namespaces, template)

print bindings_dict

#print bindings_doc.namespaces

#Add template ns to output doc!!
#print bindings_dict


exp=provconv.instantiate_template(template, bindings_dict)

outfilename=outfile
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

