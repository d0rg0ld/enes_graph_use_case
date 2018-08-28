'''
a package called provconv to support python based PROV template expansion
  (see: https://ieeexplore.ieee.org/document/7909036/)

see the associated jupyter notebooks for examples and documentation  
  
dependencies: 
    - python prov package (pip installable)
    - python3 (untested for python2)

purpose: a lightweight alternative to the java based ProvToolbox 
         (https://lucmoreau.github.io/ProvToolbox/) 
         for prototyping and for community use cases where the need to
         call an external java executible or an external REST interface 
         (e.g. https://openprovenance.org/services/view/expander )
         is disruptive to the workflow
         
Author: Stephan Kindermann
	Doron Goldfarb

History: 
      - version 0.1    (11. July 2018)
        tests based on jinja templates and function based parametrization 
      - version 0.2    (20. July)
        redesigned initial version using python prov to generate result instance.
      - version 0.3    (26. July) 
        + support for PROV instantiation files 
        + support for multiple entity expansion
      - version 0.4    (27. July)
        + support for attribute attribute expansion
        + support for provdocs without bundles
      - version 0.5    (...)  
        + application to concrete ENES use case
      - version 0.6    (28.8.2018)
	+ support tmpl:linked
	+ support vargen: namespace for auto generated uuids
	+ support expansion for relations (experimental)
        
        
Todo:
      - some more tests
      - later (if time allows): repackage functionality into object oriented 
        programming style with base classes hiding internal functionality 
        (import, export, helper functions for instantiation etc.) and 
        configurable higher level classes ..
        
Package provides:

- instantiate_template(input_template,variable_dictionary) 
  result: instantiated template

- make_binding(prov_doc,entity_dict, attr_dict):
  result: generate a PROV binding document based on an empty input document
     (with namespaces assigned) as well as variable settings for entities and
     attributes (python dictionaries) 
     
'''                        


import prov.model as prov
import six      
import itertools
import uuid
import sys
import collections

def set_namespaces(ns, prov_doc):
    '''
    set namespaces for a given provenance document (or bundle)
    Args: 
        ns (dict,list): dictionary or list of namespaces
        prov_doc : input document or bundle
    Returns:
        Prov document (or bundle) instance with namespaces set
    '''    
    
    print("here set namespace")
    
    if isinstance(ns,dict):  
        for (sn,ln) in ns.items():
            prov_doc.add_namespace(sn,ln)         
    else:
        for nsi in ns:
            prov_doc.add_namespace(nsi)     
    return prov_doc  

def make_binding(prov_doc,entity_dict,attr_dict):
    ''' 
    generate a PROV binding doc from a dict
    
    Args: 
        prov_doc (ProvDocument): input document
        entity_dict (dictionary): entity var settings
             (dict values are lists in case of multiple instantiations)
        attr_dict (dictionary): 
    Returns:
        prov_doc (ProvDocument): prov document defining a PROV binding
        
    '''    
    prov_doc.add_namespace('tmpl','<http://openprovenance.org/tmpl#>')                         
    for var,val in entity_dict.items():
       index = 0 
       if isinstance(val,list): 
           for v in val: 
               prov_doc.entity(var,{'tmpl:value'+"_"+str(index):v})
               index += 1
       else:    
            prov_doc.entity(var,{'tmpl:value':val})

    for var,val in attr_dict.items():
        index = 0
        if isinstance(val,list): 
           for v in val: 
               prov_doc.entity(var,{'tmpl:2dvalue_'+str(index)+'_0':v})
               index +=1
        else:  
               prov_doc.entity(var,{'tmpl:2dvalue_0_0':val})

    return prov_doc

def make_prov(prov_doc): 
    ''' 
    function generating an example prov document for tests and for 
    demonstration in the associated jupyter notebooks
    
    Args: 
        prov_doc (ProvDocument): input prov document with namespaces set
        
    Returns:
        prov_doc (ProvDocument): a valid complete prov document 
        (with namspaces, entities, relations and bundles   
    
    ToDo: 
       for enes data ingest use case: use information from 
       dkrz_forms/config/workflow_steps.py
   
    '''
    bundle = prov_doc.bundle('vargen:bundleid')
    #bundle.set_default_namespace('http://example.org/0/')
    #bundle = prov_doc (for test with doc without bundles)
    quote = bundle.entity('var:quote',(
         ('prov:value','var:value'),
    ))    

    author = bundle.entity('var:author',(
        (prov.PROV_TYPE, "prov:Person"),
        ('foaf:name','var:name')
    )) 

    bundle.wasAttributedTo('var:quote','var:author')
    
    return prov_doc

def save_and_show(doc,filename):
    '''
    Store and show prov document
    
    Args:
        doc (ProvDocument): prov document to store and show
        filename (string) : praefix string for filename
	Returns:
        files stored in different output formats in:
            filename.provn filename.xml, filename.rdf
        prints additionally provn serialization format    
    '''
    doc1 = make_prov(doc)
    print(doc1.get_provn())

    with open(filename+".provn", 'w') as provn_file:
        provn_file.write(doc1.get_provn())
    with open(filename+".xml",'w') as xml_file:
        xml_file.write(doc1.serialize(format='xml'))
    with open(filename+".rdf",'w') as rdf_file:
        rdf_file.write(doc1.serialize(format='rdf'))    
    
    return doc1

def make_rel(new_entity,rel, formalattrs):
	    new_rel=None
	    #handle expansion
	    
            if rel.get_type() == prov.PROV_ATTRIBUTION:
                new_rel = new_entity.wasAttributedTo(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_ASSOCIATION:
                new_rel = new_entity.wasAssociatedWith(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_DERIVATION:
                new_rel = new_entity.wasDerivedFrom(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_DELEGATION:
                new_rel = new_entity.actedOnBehalfOf(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_GENERATION:
                new_rel = new_entity.wasGeneratedBy(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_INFLUENCE:
                new_rel = new_entity.wasInfluencedBy(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_COMMUNICATION:
                new_rel = new_entity.wasInformedBy(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_USAGE:
                new_rel = new_entity.used(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_MEMBERSHIP:
                new_rel = new_entity.hadMember(*formalattrs)
                #new_rel = new_entity.hadMember(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_START:
                new_rel = new_entity.wasStartedBy(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_END:
                new_rel = new_entity.wasEndedBy(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_INVALIDATION:
                new_rel = new_entity.wasInvalidatedBy(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_ALTERNATE:
                new_rel = new_entity.alternateOf(other_attributes=rel.extra_attributes, *formalattrs)
            elif rel.get_type() == prov.PROV_SPECIALIZATION:
                new_rel = new_entity.specializationOf(other_attributes=rel.extra_attributes, *formalattrs)
            else:
                print("Warning! This relation is not yet supported. typeinfo: ",rel.get_type() )
                # ToDo: unsufficient error handling for now .. 
                new_rel = new_entity("ex:missing relation")

	    return new_rel
	

def set_rel(new_entity,rel,expAttr, linkedRelAttrs):
    '''
       helper function to add specific relations according to relation type
       implements cartesian expansion only (no "linked" restrictions) by now
    '''    

    cnt=0
    attrlists=[]
    indexlists=[]
    #create groups
    for g in linkedRelAttrs:
	alist=[]
	ilist=[]
	cnt=0
    	for a in expAttr:
		if a in g:
			alist.append(expAttr[a])
			ilist.append(cnt)
		cnt+=1
	attrlists.append(alist)
	indexlists.append(ilist)
		
	
    print repr(expAttr)
    print repr(attrlists)
    print repr(indexlists)

    outLists=[]
    for a in attrlists:
	outLists.append(zip(*a))

    #taken from http://code.activestate.com/recipes/577932-flatten-arraytuple/
    flatten = lambda arr: reduce(lambda x, y: ((isinstance(y, (list, tuple)) or x.append(y)) and x.extend(flatten(y))) or x, arr, [])

    idx=flatten(indexlists)	
    for element in itertools.product(*outLists):
	out=flatten(element)
	outordered=[out[i] for i in idx]	
	make_rel(new_entity, rel, outordered)


    #print linked

    #The maximum would be to produce the cartesian expansion of all sets in expAttr

    #return new_rel    

def set_rel_o(new_entity,rel,nfirst,nsecond, linked=False):
    '''
       helper function to add specific relations according to relation type
       implements cartesian expansion only (no "linked" restrictions) by now
    '''    

    #print linked

    if not isinstance(nfirst,list):
        nfirst = [nfirst]
    if not isinstance(nsecond,list):
        nsecond = [nsecond]
   
    if not linked: 
    	# ToDo: bad programming style - make this more intuitive 
    	nf = -1
    	for aitem in nfirst: 
    	    nf += 1
    	    ns = -1
    	    for bitem in nsecond: 
    	        ns += 1
    	        new_rel=make_rel(new_entity, rel ,nfirst[nf],nsecond[ns])
    else:
	nf=-1
	for aitem in nfirst:
		nf += 1
		new_rel=make_rel(new_entity, rel, nfirst[nf],nsecond[nf])
		
    return new_rel    

def checkLinked(nodes, instance_dict):

    tmpl_linked_qn=prov.QualifiedName(prov.Namespace("tmpl", "http://openprovenance.org/tmpl#"), "linked")
    #make tmpl:linked sweep and determine order
    # ASSUMPTION: Each entity can only be link to one "ancestor" entity, 
    #			one ancestor entity can be linked to by multiple "successor" entities
    #				NO CYCLES!
    # -> This implies: There is only one root and the network of linked rels is a directed acyclic graph

    linkedDict=dict()
    linkedGroups=list()
    for rec in nodes:
	eid = rec.identifier
	#print repr(rec.attributes)
	for attr in rec.attributes: 
		if tmpl_linked_qn == attr[0]:
			linkedDict[eid]=attr[1]
  
    dependents=[]
    roots=[]
    intermediates=[]
    for id in linkedDict:
	if id not in dependents:
		dependents.append(id)

    for id in linkedDict:
	if linkedDict[id] not in dependents:
		roots.append(linkedDict[id])
	else:
		intermediates.append(linkedDict[id])

    #print "roots: " + repr(roots)
    #print "dependents: " + repr(dependents)
    #print "intermediates: " + repr(intermediates)

    def dfs_levels(node, links, level):
	lower=dict()
	#print str(node) + " " + repr(lower)
	for k in [k for k,v in links.items() if v == node]:
		#print str(k) + " child of " + str(node)
		ret=dfs_levels(k, links, level+1)
		#print repr(ret)
		if ret!=None:
			lower.update(ret)
	myval={node : level}
	#print "Appending : " + repr(myval)
	lower.update(myval)
	#print "Returning : " + repr(lower)	
	return(lower)

    numInstances=dict()
    combRoot=dict()
    # traverse from root
    offset=0
    for r in roots:
	retval=dfs_levels(r, linkedDict, offset)
	print "root: " + str(r)

 	#get max rank
    	maxr=max(retval.values())	

	# we need to check how many entries we have
	maxEntries=0
    	for rec in nodes:
		if rec.identifier in retval:
			eid = rec.identifier
			neid = match(eid._str,instance_dict, False)
			#assume single instance bound to this node
			length=0
			if not isinstance(neid, list):
				length=1
			print repr(neid)
			print repr(eid)
			if neid==eid._str:
				# no match: if unassigned var or vargen variable, assume length 0
				length=0
				print "same"
			if length>maxEntries:
				maxEntries=length
			print length
			if isinstance(neid,list):
				# list is assigned to node, now all lengths must be equal
				length=len(neid)
				if length!=maxEntries:
					if maxEntries>0:
						print length
						print maxEntries
						print "Linked entities must have same number of bound instances!"
						sys.exit(1)
					maxEntries=length
	#	if rec.identifier not in combRoot:
	#		retval[rec.identifier]=maxr+1

	for n in retval:
		numInstances[n]=maxEntries
	combRoot.update(retval)
	linkedGroups.append(retval)
	offset=maxr+1

    for rec in nodes:
	if rec.identifier not in combRoot:
		combRoot[rec.identifier]=offset
		linkedGroups.append({rec.identifier : offset})
		eid=rec.identifier
		neid = match(eid._str,instance_dict, False)
		if isinstance(neid, list):
			numInstances[eid]=len(neid)
		else:
			numInstances[eid]=1
	#need to remember number of instances for each var
	# when multiple link groups rank accordingly
	

    #print repr(combRoot)
    #try reorder nodes based on tmpl:linked hierarchy	
    #nodes_sorted=sorted(nodes, key=retval.get)  
 
    fnc=lambda x: combRoot[x.identifier]
    nodes_sorted=sorted(nodes, key=fnc)
    for rec in nodes_sorted:
	print "SORT : " + str(rec.identifier)
  
    print repr(linkedGroups)

    return { "nodes" : nodes_sorted, "numInstances" : numInstances, "linkedGroups" : linkedGroups}


def prop_select(props,n):
    '''
    helper function to select individual values if dict value is a list
    '''
    nprops = {}
    #print("Props and n: ",props,n)
    for key,val in props.items():
        if isinstance(val,list):
	    #print "---------------"
	    #print len(val) 
	    #
	    # BRUTE FORCEprint n
	    # BRUTE FORCE
	    if len(val)==1:
		n=0
            nprops[key] = val[n]
        else:
            nprops[key] = val 
    return nprops        

def add_records(old_entity, new_entity, instance_dict):
    '''
    function adding instantiated records (entities and relations) to a 
    prov document and containing bundles
    
    calls the match() and attr_match() functions for the instantiation
    
    Args:
        old_entity (bundle or ProvDocument): Prov template for structre info
        
        new_entity (bundle or ProvDocument): Instantiated entity with matched 
          records (entities and relations)
           
        instance_dict: Instantiation dictionary   
    Returns:   
        new_entity (bundle or ProvDocument): Instantiated entity
        
    Todo: change return values of functions (this one and the ones called)    
    
    '''
    
    print("Here add recs")
    
    relations = []
    nodes = []
    
    # for late use:
    # node_label = six.text_type(record.identifier)
    # uri = record.identifier.uri
    # uri = qname.uri

    for rec in old_entity.records:
        if rec.is_element():
           nodes.append(rec)
           #print(rec)
        elif rec.is_relation():
           relations.append(rec)
        else:
            print("Warning: Unrecognized element type: ",rec)

    linkedInfo=checkLinked(nodes, instance_dict)
    nodes_sorted=linkedInfo["nodes"]
    numInstances=linkedInfo["numInstances"]
    linkedGroups=linkedInfo["linkedGroups"]

    for rec in nodes_sorted:
        eid = rec.identifier
        attr = rec.attributes
        args = rec.args
	#print(attr)
	
	#print eid._str
	#dirty trick
        neid = match(eid._str,instance_dict, True, numInstances[eid])
	#print(repr(instance_dict))
        props = attr_match(attr,instance_dict)
	#print "-------------------"
      	#print repr(neid)
	#print "-------------------"
	#print repr(props)
	#here we cann inject vargen things if there is a linked attr 
        if isinstance(neid,list):
            i = 0
            for n in neid: 
                new_node = new_entity.entity(prov.Identifier(n),other_attributes=prop_select(props,i))
                i += 1
        else:
             new_node = new_entity.entity(prov.Identifier(neid),other_attributes=props)

    for rel in relations:

	# We need to consider the following things:

	# id: opt Id
	
	# c: collection

	# e: entity
	# e1: entity
	# e2: entity
	# alt1: entity
	# alt2: entity
	# infra: entity
	# supra: entity

	# a: activity
	# a1: activity
	# a2: activity
	# g2: generation activity
	# u1: usage activity

	# ag: agent
	# ag1: agent
	# ag2: agent
	
	# pl: plan

	# t: time

	#generation	wasGeneratedBy(id;e,a,t,attrs)
	#Usage		used(id;a,e,t,attrs)
	#Communication	wasInformedBy(id;a2,a1,attrs)
	#Start		wasStartedBy(id;a2,e,a1,t,attrs)
	#End		wasEndedBy(id;a2,e,a1,t,attrs)
	#Invalidation	wasInvalidatedBy(id;e,a,t,attrs)
	
	#Derivation	wasDerivedFrom(id; e2, e1, a, g2, u1, attrs)
	
	#Attribution	wasAttributedTo(id;e,ag,attr)
	#Association	wasAssociatedWith(id;a,ag,pl,attrs)
	#Delegation	actedOnBehalfOf(id;ag2,ag1,a,attrs)	
	#Influence	wasInfluencedBy(id;e2,e1,attrs)
	
	#Alternate	alternateOf(alt1, alt2)
	#Specialization	specializationOf(infra, supra)
	
	#Membership	hadMember(c,e)	

	#print repr(rel)
	#print repr(rel.attributes)
	
	#expand all possible formal attributes
	linkedMatrix=collections.OrderedDict()
	expAttr=collections.OrderedDict()
	for fa1 in rel.formal_attributes:
		linkedMatrix[fa1[0]]=collections.OrderedDict()
		for fa2 in rel.formal_attributes:
			linkedMatrix[fa1[0]][fa2[0]]=False
			for group in linkedGroups:
				if fa1[1] in group and fa2[1] in group: 
					linkedMatrix[fa1[0]][fa2[0]]=True	
		if fa1[1] != None:
			expAttr[fa1[0]]=match(fa1[1], instance_dict, False)
			if not isinstance(expAttr[fa1[0]], list):
				expAttr[fa1[0]]=[expAttr[fa1[0]]]
		else:
			expAttr[fa1[0]]=[None]
	
	#we also want grouped relation attribute names
	linkedRelAttrs=[]
	for group in linkedGroups:
		lst=[]
		for fa1 in rel.formal_attributes:
			if fa1[1] in group:
				lst.append(fa1[0])
		if len(lst)>0:
			linkedRelAttrs.append(lst)
	
	

	
	print "------------------------------------------------"
	
	print "THIS : "  + repr(expAttr)
	"""
	print "------------------------------------------------"
	for f1 in linkedMatrix:
		print "\t" + str(f1),
	print
	for f1 in linkedMatrix:
		print str(f1) + "\t",
		for f2 in linkedMatrix:
			print str(linkedMatrix[f1][f2]) + "\t",
		print
	"""
	print "------------------------------------------------"

	print repr(linkedRelAttrs)

        args = rel.args
	if prnt:
        	print (repr(args))
        #(first,second, third) = args     
        #(nfirst,nsecond) = (match_qn(first,instance_dict),match_qn(second,instance_dict))     

	linked=False
	for group in linkedGroups:
		#print "IS " + str(args[0]) + " linked with  " + str(args[1])
		if args[0] in group and args[1] in group:
			#print repr(group)
			#print str(args[0]) + " linked with  " + str(args[1])
			linked=True
			break
      
        (nfirst,nsecond) = (match(args[0],instance_dict, False),match(args[1],instance_dict, False))     

	#NOT required
	"""
	linked=False
	#highly unefficient
	firstLink=None
	first=nfirst
	if isinstance(first, list):
		first=first[0]
	for n in new_entity.records:
		if n.identifier==first:
			#print str(n.identifier) + " " + str(first)
			#print repr(n.attributes)
			for a in n.attributes:
				if tmpl_linked_qn == a[0]:
					print "Found link for " + str(first) + " " + str(a[1])
					firstLink=a[1]
	secondLink=None
	second=nsecond
	if isinstance(second, list):
		second=second[0]
	print str(first) + "  ---  " + str(second)
	for n in new_entity.records:
		if n.identifier==second:
			for a in n.attributes:
				if tmpl_linked_qn == a[0]:
					print "Found link for " + str(second) + " " + str(a[1])
					secondLink= a[1]

	print repr(firstLink) + "   " + repr(secondLink)
	
	if (firstLink != None or secondLink != None) and ( firstLink==second or secondLink==first):
		linked=True
	"""

	#We need to check if instances are linked    
        new_rel = set_rel(new_entity,rel,expAttr,linkedRelAttrs)        
        #new_rel = set_rel_o(new_entity,rel,nfirst,nsecond, linked)        
    return new_entity   


# To Do: condense matching functionality into one function/class
# To To: handle http prefix attributes: partition into namespace, localpart 
#        transform to QualifiedName
def match_qn(qn,mdict):
    '''
    helper function for Prov QualifiedName matching 
    (temporary workaround ..)
    
    Args: 
        qn (QualifiedName): A prov QualifiedName
        mdict (dict) : a dictionary to match with
    Returns:
        target (String): the result of matching the QualifiedName
             (same as input or value of matching key in dict)            
    '''
    lp = qn.localpart
    ns = qn.namespace.prefix
    source = ns+":"+lp
    #print "qn: " + source
    target = match(source,mdict, False)
    return target

def match(eid,mdict, node, numEntries=1):
    '''
    helper function to match strings based on dictionary
    
    Args:
        eid (string): input string
        mdict (dict): match dictionary
    Returns:
        meid: same as input or matching value for eid key in mdict
    '''
    adr=eid
    if isinstance(adr,prov.QualifiedName):
	lp = adr.localpart
	ns = adr.namespace.prefix
	adr=ns+":"+lp
    #override: vargen found in entity declaration position: create a uuid
    #print "match " + repr(adr) + " with " + str(adr) + " red " + str(adr)[:7]
    #not optimal, need ability to provide custom namespace
    if node and "vargen:" in str(adr) and str(adr)[:7]=="vargen:":
	ret=None
	for e in range(0,numEntries):
		uid=str(uuid.uuid4())
		if adr not in mdict:
			ret=prov.QualifiedName(prov.Namespace("ex", "http://example.com#"), uid)
			mdict[adr]=ret
		else:
			if not isinstance(mdict[adr], list):
				tmp=list()
				tmp.append(mdict[adr])
				mdict[adr]=tmp
				tmp2=list()
				tmp2.append(ret)
				ret=tmp2
			qn=prov.QualifiedName(prov.Namespace("ex", "http://example.com#"), uid)
			mdict[adr].append(qn)
			ret.append(qn)
	return ret
    if adr in mdict:
        #print("Match: ",adr)
        madr = mdict[adr]
    else:
        #print("No Match: ",adr)
        madr = eid 
    return madr

def attr_match(attr_list,mdict):
    '''
    helper function to match a tuple list
    Args:
        attr_list (list): list of qualified name tuples
        mdict (dict): matching dictionary
        
    ToDo: improve attr_match and match first version helper functions    
    '''      
    p_dict = {}
    for (pn,pv)  in attr_list:
	#print "pn: " + repr(pn) + " pv: " + repr(pv)
        npn_new = match(pn,mdict, False)  
	#print "npn_new: " + repr(npn_new)
        p_dict[npn_new] = match(pv,mdict, False)
        #print("Attr dict:",p_dict)
    return p_dict 
#---------------------------------------------------------------

def instantiate_template(prov_doc,instance_dict):
    '''
    Instantiate a prov template based on a dictionary setting for
    the prov template variables
    
    Supported:
        entity and attribute var: matching
        multiple entity expansion
        
    Unsupported by now:
        linked entities
        multiple attribute expansion
        
    To Do: Handle core template expansion rules as described in
           https://ieeexplore.ieee.org/document/7909036/ 
           and maybe add additional expansion/composition rules for
           templates useful to compose ENES community workflow templates
           
    Args: 
        prov_doc (ProvDocument): input prov document template
        instance_dict (dict): match dictionary
    ''' 
    
    print("here inst templ")
    
    new_doc = set_namespaces(prov_doc.namespaces,prov.ProvDocument()) 
    
    new_doc = add_records(prov_doc,new_doc,instance_dict)
    
    blist = list(prov_doc.bundles)
   
    for bundle in blist:       
        new_bundle = new_doc.bundle(bundle.identifier)               
        new_bundle = add_records(bundle, new_bundle,instance_dict)      
            
    return new_doc
