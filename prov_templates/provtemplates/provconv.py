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

def set_rel(new_entity,rel,nfirst,nsecond):
    '''
       helper function to add specific relations according to relation type
       implements cartesian expansion only (no "linked" restrictions) by now
    '''    
    if not isinstance(nfirst,list):
        nfirst = [nfirst]
    if not isinstance(nsecond,list):
        nsecond = [nsecond]
    
    # ToDo: bad programming style - make this more intuitive 
    nf = -1
    for aitem in nfirst: 
        nf += 1
        ns = -1
        for bitem in nsecond: 
            ns += 1
            
            if rel.get_type() == prov.PROV_ATTRIBUTION:
                new_rel = new_entity.wasAttributedTo(nfirst[nf],nsecond[ns])
            elif rel.get_type() == prov.PROV_ASSOCIATION:
                new_rel = new_entity.wasAssociatedWith(nfirst[nf],nsecond[ns])
            elif rel.get_type() == prov.PROV_DERIVATION:
                new_rel = new_entity.wasDerivedFrom(nfirst[nf],nsecond[ns])
            elif rel.get_type() == prov.PROV_DELEGATION:
                new_rel = new_entity.actedOnBehalfOf(nfirst[nf],nsecond[ns])
            elif rel.get_type() == prov.PROV_GENERATION:
                new_rel = new_entity.wasGeneratedBy(nfirst[nf],nsecond[ns])
            elif rel.get_type() == prov.PROV_INFLUENCE:
                new_rel = new_entity.wasInfluencedBy(nfirst[nf],nsecond[ns])
            elif rel.get_type() == prov.PROV_COMMUNICATION:
                new_rel = new_entity.wasInformedBy(nfirst[nf],nsecond[ns])
            elif rel.get_type() == prov.PROV_USAGE:
                new_rel = new_entity.used(nfirst[nf],nsecond[ns])
            elif rel.get_type() == prov.PROV_MEMBERSHIP:
                new_rel = new_entity.hadMember(nfirst[nf],nsecond[ns])
            else:
                print("Warning! This relation is not yet supported. typeinfo: ",rel.get_type() )
                # ToDo: unsufficient error handling for now .. 
                new_rel = new_entity("ex:missing relation")
    return new_rel    

def prop_select(props,n):
    '''
    helper function to select individual values if dict value is a list
    '''
    nprops = {}
    #print("Props and n: ",props,n)
    for key,val in props.items():
        if isinstance(val,list):
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

    for rec in nodes:
        eid = rec.identifier
        attr = rec.attributes
        args = rec.args
        props = attr_match(attr,instance_dict)
	print eid._str
        neid = match(eid._str,instance_dict, True)
        
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

	print repr(rel)
	print repr(rel.attributes)

	prnt=False
	if 1:
            if rel.get_type() == prov.PROV_GENERATION:
		if prnt:
			print "ID: " + str(rel.identifier)
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	
            elif rel.get_type() == prov.PROV_USAGE:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	
            elif rel.get_type() == prov.PROV_COMMUNICATION:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	
            elif rel.get_type() == prov.PROV_START:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	
            elif rel.get_type() == prov.PROV_END:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	
            elif rel.get_type() == prov.PROV_INVALIDATION:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	

            elif rel.get_type() == prov.PROV_DERIVATION:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	

            if rel.get_type() == prov.PROV_ATTRIBUTION:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	
            elif rel.get_type() == prov.PROV_ASSOCIATION:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	
            elif rel.get_type() == prov.PROV_DELEGATION:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	
            elif rel.get_type() == prov.PROV_INFLUENCE:
		if prnt:
			print "ID: " + str(rel.identifier)	
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	

            elif rel.get_type() == prov.PROV_ALTERNATE:
		if prnt:
			print repr(rel)
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	
            elif rel.get_type() == prov.PROV_SPECIALIZATION:
		if prnt:
			print repr(rel)
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	

            elif rel.get_type() == prov.PROV_MEMBERSHIP:
		if prnt:
			print repr(rel)
			print repr(rel.formal_attributes)	
			print repr(rel.extra_attributes)	

	fa_tup=[]
	for fa in rel.formal_attributes:
		if fa[1] != None:
			fa_tup.append(tuple([fa[0], match(fa[1], instance_dict, False)],))
		else:
			fa_tup.append((fa[0], None))
	if prnt:
		print "THIS : "  + repr(tuple(fa_tup))

        args = rel.args
	if prnt:
        	print (repr(args))
        #(first,second, third) = args     
        #(nfirst,nsecond) = (match_qn(first,instance_dict),match_qn(second,instance_dict))           
        (nfirst,nsecond) = (match(args[0],instance_dict, False),match(args[1],instance_dict, False))           
        new_rel = set_rel(new_entity,rel,nfirst,nsecond)        
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

def match(eid,mdict, node):
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
	uid=str(uuid.uuid4())
	if adr not in mdict:
		mdict[adr]=[]
	mdict[adr].append(prov.QualifiedName(prov.Namespace("ex", "http://example.com#"), uid))
	return prov.QualifiedName(prov.Namespace("ex", "http://example.com#"), uid)
    if adr in mdict:
        #print("Match: ",adr)
        madr = mdict[adr]
    else:
        #print("No Match: ",adr)
        madr = adr
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
	print "pn: " + repr(pn) + " pv: " + repr(pv)
        npn_new = match(pn,mdict, False)  
	print "npn_new: " + repr(npn_new)
        p_dict[npn_new] = match(pv,mdict, False)
        print("Attr dict:",p_dict)
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
