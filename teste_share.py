import os
from fnmatch import fnmatch
from itertools import chain
import win32api
import win32security
import ntsecuritycon
import pywintypes


def glob_path_match(path, pattern_list):
    """
    Checks if path is in a list of glob style wildcard paths
    :param path: path of file / directory
    :param pattern_list: list of wildcard patterns to check for
    :return: Boolean
    """
    return any(fnmatch(path, pattern) for pattern in pattern_list)


def get_files_recursive(root, d_exclude_list=None, f_exclude_list=None,
                    ext_exclude_list=None, ext_include_list=None,
                    depth=0, primary_root=None, fn_on_perm_error=None,
                    include_dirs=False):
    '''
    Walk a path to recursively find files
    Modified version of https://stackoverflow.com/a/24771959/2635443 that includes exclusion lists
    and accepts glob style wildcards on files and directories
    :param root: (str) path to explore
    :param include_dirs: (bool) should output list include directories
    :param d_exclude_list: (list) list of root relative directories paths to exclude
    :param f_exclude_list: (list) list of filenames without paths to exclude
    :param ext_exclude_list: list() list of file extensions to exclude, ex: ['.log', '.bak'],
           takes precedence over ext_include_list
    :param ext_include_lsit: (list) only include list of file extensions, ex: ['.py']
    :param depth: (int) depth of recursion to acheieve, 0 means unlimited, 1 is just the current dir...
    :param primary_root: (str) Only used for internal recursive exclusion lookup, don't pass an argument here
    :param fn_on_perm_error: (function) Optional function to pass, which argument will be the file / directory that has permission errors
    :return: list of files found in path
    '''

    # Make sure we don't get paths with antislashes on Windows
    if os.path.isdir(root):
        root = os.path.normpath(root)
    else:
        return root

    # Check if we are allowed to read directory, if not, try to fix permissions if fn_on_perm_error is passed
    try:
        os.listdir(root)
    except PermissionError:
        if fn_on_perm_error is not None:
            fn_on_perm_error(root)

    # Make sure we clean d_exclude_list only on first function call
    if primary_root is None:
        if d_exclude_list is not None:
            # Make sure we use a valid os separator for exclusion lists
            d_exclude_list = [os.path.normpath(d) for d in d_exclude_list]
        else:
            d_exclude_list = []
    if f_exclude_list is None:
        f_exclude_list = []
    if ext_exclude_list is None:
        ext_exclude_list = []

def _find_files():
    try:
        if include_dirs:
            yield root
        for f in os.listdir(root):
            file_ext = os.path.splitext(f)[1]
            if os.path.isfile(os.path.join(root, f)) and not glob_path_match(f, f_exclude_list) \
                and file_ext not in ext_exclude_list \
                and (file_ext in ext_include_list if ext_include_list is not None else True):
                yield os.path.join(root, f)

    except PermissionError:
        pass

def _find_files_in_dirs(depth):
    if depth == 0 or depth > 1:
        depth = depth - 1 if depth > 1 else 0
        try:
            for d in os.listdir(root):
                d_full_path = os.path.join(root, d)
                if os.path.isdir(d_full_path):
                    # p_root is the relative root the function has been called with recursively
                    # Let's check if p_root + d is in d_exclude_list
                    p_root = os.path.join(primary_root, d) if primary_root is not None else d
                    if not glob_path_match(p_root, d_exclude_list):
                        files_in_d = get_files_recursive(d_full_path,
                                                         d_exclude_list=d_exclude_list,
                                                         f_exclude_list=f_exclude_list,
                                                         ext_exclude_list=ext_exclude_list,
                                                         ext_include_list=ext_include_list,
                                                         depth=depth, primary_root=p_root,
                                                         fn_on_perm_error=fn_on_perm_error,
                                                         include_dirs=include_dirs)
                        if include_dirs:
                            yield d
                        if files_in_d:
                            for f in files_in_d:
                                yield f

        except PermissionError:
            pass

    # Chain both generators
    return chain(_find_files(), _find_files_in_dirs(depth))


def get_binary_sid(string=None):
    """
    Wrapper function that returns PySID object from SID identifier or username
    If none given, we'll get current user

    :param string: (str) SID identifier or username
    :return: (PySID) object
    """
    if string is None:
        string = win32api.GetUserName()
    if string.startswith('S-1-'):
        # Consider we deal with a sid string
        return win32security.GetBinarySid(string)
    else:
        # Try to resolve username
        # LookupAccountName returns tuple (user, domain, type)

        try:
            user, _, _ = win32security.LookupAccountName('', string)
            print(user)
            return user
        except pywintypes.error as e:
            raise OSError('Cannot map security ID: {0} with name. {1}'.format(string, e))


def set_file_owner(path, owner=None, force=False):
    """
    Set owner on NTFS files / directories
    https://stackoverflow.com/a/61009508/2635443

    :param path: (str) path
    :param owner: (PySID) object that represents the security identifier. If not set, current security identifier will be used
    :param force: (bool) Shall we force take ownership
    :return:
    """
    try:
        hToken = win32security.OpenThreadToken(win32api.GetCurrentThread(),
                                               win32security.TOKEN_ALL_ACCESS, True)

    except win32security.error:
        hToken = win32security.OpenProcessToken(win32api.GetCurrentProcess(),
                                                win32security.TOKEN_ALL_ACCESS)
    if owner is None:
        owner = win32security.GetTokenInformation(hToken, win32security.TokenOwner)
    prev_state = ()
    if force:
        new_state = [(win32security.LookupPrivilegeValue(None, name),
                      win32security.SE_PRIVILEGE_ENABLED)
                     for name in (win32security.SE_TAKE_OWNERSHIP_NAME,
                                  win32security.SE_RESTORE_NAME)]
        prev_state = win32security.AdjustTokenPrivileges(hToken, False,
                                                         new_state)
    try:
        sd = win32security.SECURITY_DESCRIPTOR()
        sd.SetSecurityDescriptorOwner(owner, False)
        win32security.SetFileSecurity(path, win32security.OWNER_SECURITY_INFORMATION, sd)
    except pywintypes.error as e:
        # Let's raise OSError so we don't need to import pywintypes in parent module to catch the exception
        raise OSError('Cannot take ownership of file: {0}. {1}.'.format(path, e))
    finally:
        if prev_state:
            win32security.AdjustTokenPrivileges(hToken, False, prev_state)


def easy_permissions(permission):
    """
    Creates ntsecuritycon permission bitmask from simple rights

    :param permission: (str) Simple R, RX, RWX, F  rights
    :return: (int) ntsecuritycon permission bitmask
    """
    permission = permission.upper()
    if permission == 'R':
        return ntsecuritycon.GENERIC_READ
    if permission == 'RX':
        return ntsecuritycon.GENERIC_READ | ntsecuritycon.GENERIC_EXECUTE
    if permission in ['RWX', 'M']:
        return ntsecuritycon.GENERIC_READ | ntsecuritycon.GENERIC_WRITE | ntsecuritycon.GENERIC_EXECUTE
    if permission == 'F':
        return ntsecuritycon.GENERIC_ALL
    raise ValueError('Bogus easy permission')


def set_acls(path, user_list=None, group_list=None, owner=None, permission=None, inherit=False, inheritance=False):
    """
    Set Windows DACL list

    :param path: (str) path to directory/file
    :param user_sid_list: (list) str usernames or PySID objects
    :param group_sid_list: (list) str groupnames or PySID objects
    :param owner: (str) owner name or PySID obect
    :param permission: (int) permission bitmask
    :param inherit: (bool) inherit parent permissions
    :param inheritance: (bool) apply ACL to sub folders and files
    """
    if inheritance:
        inheritance_flags = win32security.CONTAINER_INHERIT_ACE | win32security.OBJECT_INHERIT_ACE
    else:
        inheritance_flags = win32security.NO_INHERITANCE

    security_descriptor = {'AccessMode': win32security.GRANT_ACCESS,
                           'AccessPermissions': 0,
                           'Inheritance': inheritance_flags,
                           'Trustee': {'TrusteeType': '',
                                       'TrusteeForm': win32security.TRUSTEE_IS_SID,
                                       'Identifier': ''}
                           }

    # Now create a security descriptor for each user in the ACL list
    security_descriptors = []

    # If no user / group is defined, let's take current user
    if user_list is None and group_list is None:
        user_list = [get_binary_sid()]

    if user_list is not None:
        for sid in user_list:
            sid = get_binary_sid(sid)
            s = security_descriptor
            s['AccessPermissions'] = permission
            s['Trustee']['TrusteeType'] = win32security.TRUSTEE_IS_USER
            s['Trustee']['Identifier'] = sid
            security_descriptors.append(s)

    if group_list is not None:
        for sid in group_list:
            sid = get_binary_sid(sid)
            s = security_descriptor
            s['AccessPermissions'] = permission
            s['Trustee']['TrusteeType'] = win32security.TRUSTEE_IS_GROUP
            s['Trustee']['Identifier'] = sid
            security_descriptors.append(s)

    try:
        sd = win32security.GetNamedSecurityInfo(path, win32security.SE_FILE_OBJECT,
                                                win32security.DACL_SECURITY_INFORMATION | win32security.UNPROTECTED_DACL_SECURITY_INFORMATION)
    except pywintypes.error as e:
        raise OSError('Failed to read security for file: {0}. {1}'.format(path, e))
    dacl = sd.GetSecurityDescriptorDacl()
    dacl.SetEntriesInAcl(security_descriptors)

    security_information_flags = win32security.DACL_SECURITY_INFORMATION

    if not inherit:
        # PROTECTED_DACL_SECURITY_INFORMATION disables inheritance from parent
        security_information_flags = security_information_flags | win32security.PROTECTED_DACL_SECURITY_INFORMATION
    else:
        security_information_flags = security_information_flags | win32security.UNPROTECTED_DACL_SECURITY_INFORMATION

    # If we want to change owner, SetNamedSecurityInfo will need win32security.OWNER_SECURITY_INFORMATION in SECURITY_INFORMATION
    if owner is not None:
        security_information_flags = security_information_flags | win32security.OWNER_SECURITY_INFORMATION
        if isinstance(owner, str):
            owner = get_binary_sid(owner)

    try:
        # SetNamedSecurityInfo(path, object_type, security_information, owner, group, dacl, sacl)
        win32security.SetNamedSecurityInfo(path, win32security.SE_FILE_OBJECT,
                                           security_information_flags,
                                           owner, None, dacl, None)
    except pywintypes.error as e:
        raise OSError


def take_ownership_recursive(path, owner=None):
    def take_own(path):
        nonlocal owner
        try:
            set_file_owner(path, owner=owner, force=True)
        except OSError:
            print('Permission error on: {0}.'.format(path))

    files = get_files_recursive(path, include_dirs=True, fn_on_perm_error=take_own)
    for file in files:
        set_file_owner(file, force=True)


def get_files_recursive_and_set_permissions(path, owner=None, permissions=None, user_list=None):
    def fix_perms(path):
        nonlocal permissions
        nonlocal owner
        nonlocal user_list
        if permissions == None:
            permissions = easy_permissions('F')
        print('Permission error on: {0}.'.format(path))
        try:
            set_acls(path, user_list=user_list, owner=owner, permission=permissions, inheritance=False)
        except OSError:
            # Lets force ownership change
            try:
                set_file_owner(path, force=True)
                # Now try again
                set_acls(path, user_list=user_list, owner=owner, permission=permissions, inheritance=False)
            except OSError as e:
                print('Cannot fix permission on {0}. {1}'.format(path, e))

    files = get_files_recursive(path, include_dirs=True, fn_on_perm_error=fix_perms)
    for file in files:
        set_acls(file, user_list=user_list, owner=owner, permission=easy_permissions('F'), inheritance=False)
