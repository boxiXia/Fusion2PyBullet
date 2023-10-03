# -*- coding: utf-8 -*-
""" 
Copy to new components and export stls.

@syuntoku
@yanshil
"""

import adsk, adsk.core, adsk.fusion
import os.path, re
from xml.etree import ElementTree
from xml.dom import minidom


def get_valid_filename(s: str) -> str:
    # If the input string contains substring 'base_link', return 'base_link'
    if 'base_link' in s:
        s1 = 'base_link'
    else:
        # Remove leading and trailing spaces
        s1 = s.strip()
        # remove [:d] version number
        s1 = re.sub(r' v\d+', '', s1)
        # remove consecutive spaces
        s1 = re.sub(r'\s+', ' ', s1)
        # replace illegal characters with an underscore
        s1 = re.sub(r'[\/:*?"<>| +]', '_', s1)
        # replace consecutive underscores with a single underscore
        s1 = re.sub(r'_+', '_', s1)
    return s1


# copy and export
def copy_occs_and_export(root,design, save_dir, components):
    """    
    duplicate all the components
    """    
    ## NOTE: Set "Do not capture design history" NEEDED TO MAKE bRepBodies
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
        
    # create a single exportManager instance
    exportMgr = design.exportManager
    # get the script location
    try: os.mkdir(save_dir + '/meshes')
    except: pass
    scriptDir = save_dir + '/meshes'  

    allOccs = root.occurrences
    coppy_list = [occs for occs in root.allOccurrences]
    for occs in coppy_list:
        if occs.bRepBodies.count > 0:
            occs.isGrounded=True
            bodies = occs.bRepBodies
            transform = adsk.core.Matrix3D.create()
            # Create new components from occs
            # This support even when a component has some occses. 
            new_occs = allOccs.addNewComponent(transform)  # this create new occs
            key = get_valid_filename(occs.fullPathName)
            new_occs.component.name = 'TMP_'+key
            # new_occs = allOccs.item((allOccs.count-1))
            for i in range(bodies.count):
                body = bodies.item(i)
                body.copyToComponent(new_occs)
            try:
                print("Export file: {}".format(key))
                # fileName = scriptDir + "/" + occ.component.name
                fileName = scriptDir + "/" + key
                # create stl exportOptions
                stlExportOptions = exportMgr.createSTLExportOptions(new_occs, fileName)
                stlExportOptions.sendToPrintUtility = False
                stlExportOptions.isBinaryFormat = True
                # options are .MeshRefinementLow .MeshRefinementMedium .MeshRefinementHigh
                stlExportOptions.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementLow
                exportMgr.execute(stlExportOptions)
            except:
                print('Component ' + occs.component.name + ' has something wrong.')


def file_dialog(ui):     
    """
    display the dialog to save the file
    """
    # Set styles of folder dialog.
    folderDlg = ui.createFolderDialog()
    folderDlg.title = 'Fusion Folder Dialog' 
    
    # Show folder dialog
    dlgResult = folderDlg.showDialog()
    if dlgResult == adsk.core.DialogResults.DialogOK:
        return folderDlg.folder
    return False


def origin2center_of_mass(inertia, center_of_mass, mass):
    """
    convert the moment of the inertia about the world coordinate into 
    that about center of mass coordinate


    Parameters
    ----------
    moment of inertia about the world coordinate:  [xx, yy, zz, xy, yz, xz]
    center_of_mass: [x, y, z]
    
    
    Returns
    ----------
    moment of inertia about center of mass : [xx, yy, zz, xy, yz, xz]
    """
    x = center_of_mass[0]
    y = center_of_mass[1]
    z = center_of_mass[2]
    translation_matrix = [y**2+z**2, x**2+z**2, x**2+y**2,
                         -x*y, -y*z, -x*z]
    return [ i - mass*t for i, t in zip(inertia, translation_matrix)]


def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.
    Parameters
    ----------
    elem : xml.etree.ElementTree.Element
    
    
    Returns
    ----------
    pretified xml : str
    """
    rough_string = ElementTree.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

