#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function

import argparse
import os 
import sys
from oc_cdtapi.NexusAPI import *

def get_args():
    """
    Function for command line arguments parsing
    """
    parser = argparse.ArgumentParser(description="Simple Nexus API CLI")
    parser.add_argument("-url", "--mvn_url", type=str, help="Specify Nexus' URL (mandatory if MVN_URL environment variable is not set)")
    parser.add_argument("-urepo", "--upload_repo", type=str, help="Specify the upload repo")
    parser.add_argument("-drepo", "--download_repo", type=str, help="Specify the download repo")
    parser.add_argument("-user", "--mvn_user", type=str, help="Specify the Nexus username")
    parser.add_argument("-pass", "--mvn_password", type=str, help="Specify the Nexus user's password")
    parser.add_argument("gav", nargs="*", help="Specify one or multiple GAVs")
    parser.add_argument("-p", "--path", type=str, help="Specify the download path (default = current directory) or set the file path for upload")
    parser.add_argument("-f", "--filename", type=str, nargs="*", help="Specify the output filename(s) for download artifact(s)")
    parser.add_argument("-info", "--info", action = "store_true", help="Set the flag if you want to get info for the given GAV(s)")
    parser.add_argument("-d", "--download", action = "store_true", help="Set the flag if you want to instantly download given artifacts")
    parser.add_argument("-u", "--upload", action = "store_true", help="Set the flag if you want to instantly upload given artifact")
    parser.add_argument("-del", "--delete",action = "store_true", help="Set the flag if you want to delete given artifacts")
    parser.add_argument("--fail-on-artifact-exists", dest = 'no_check_exist', default = False, action = 'store_true', help = "Fail if artifact allready exists (otherwise - silently ignore it)")
    args = parser.parse_args()
    
    return parser,args

class ArtifactTool():
    """
    Simple command-line interface for working with Nexus API
    """

    def __init__(self, mvn_url=None, mvn_user=None, mvn_pass=None, testing=False):
        if testing:
            return
        
        self.API = NexusAPI(root=mvn_url, user=mvn_user, auth=mvn_pass)

    def get_info(self, gavs, download_repo=None):
        """
        Show information about the given GAV(s)
        """
        if not gavs:
            raise ValueError("No GAV was specified")

        for i in gavs:
            # and information itself in the console
            print(u"=======")
            print(u"GAV:\t'%s'" % i)
            print(u"Repo:\t'%s'" % (download_repo if download_repo else self.API.repo_default))
            print(u"URL:\t'%s'" % self.API.gav_get_url(i, download_repo))
            _exists = self.API.exists(i, repo=download_repo)
            print(u"Exists:\t'%s'" % str(_exists))

            if not _exists:
                return

            _info = self.API.info(i, download_repo)
            _ls = self.API.ls(i, download_repo)

            if _info:
                print(u"MD5:\t'%s'" % _info.get("md5"))
                print(u"MIME:\t'%s'" % _info.get("mime"))

            if _ls:
                print(u"LIST:\n '%s'" % "\n ".join(_ls))

    def check_existence(self, gav, repo=None):
        """
        Checks that the given GAV exists in the repository
        """
        # exception will be raised on caller methods (or here if GAV format is incorrect)
        return self.API.exists(gav, repo)

    def download_artifact(self, gavs, path=None, download_repo=None, result_filenames=None):
        """
        Downloads all given artifacts to the specified path
        """
        if not path:
            path = os.path.realpath(".")
        
        if not os.path.isdir(path):
            raise ValueError("Incorrect output path was specified.")

        if not gavs:
            raise ValueError("No GAV was specified")

        if result_filenames and len(gavs) != len(result_filenames):
            raise ValueError("GAVs and filenames quantity does not match")

        for i in gavs:
            if not self.check_existence(i, download_repo):
                raise FileNotFoundError(i)

            if not result_filenames:
                filename = gav_to_filename(i)
            else:
                filename = result_filenames[gavs.index(i)]

            with open(os.path.realpath(os.path.expanduser(path) + os.path.sep + filename), "wb") as output_file:
                self.API.cat(i, binary=True, stream=True, repo=download_repo, write_to=output_file)
                
            print(u"Downloaded: '{}' ==> '{}'".format(os.path.basename(i), filename))

    def delete_artifact(self, gavs=None, upload_repo=None):
        """
        Deletes one or multiple artifacts using their GAVs
        """
        if not gavs:
            raise ValueError("No GAV was specified")

        for i in gavs:
            print(self.API.remove(gav=i, repo=upload_repo))

    def upload_artifact(self, gav=None, path=None, upload_repo=None, no_check = True):
        """
        Uploads a new artifact
        """
        if not gav:
            raise ValueError("No GAV was specified")

        gav = gav[0]

        if not no_check and (self.check_existence(gav) or self.check_existence(gav, upload_repo)):
            print(u"'%s' already exists, skipping upload" % gav)
            return

        if path: 
            path = os.path.expanduser(path)
        
        if (not path) or (not os.path.isfile(path)):
            raise ValueError("Incorrect file was specified for upload")

        with open(os.path.realpath(path), "rb") as artifact:
            resp = self.API.upload(gav, data=artifact, metadata=True, repo=upload_repo)

        if "<Response [201]>" in str(resp):
            print(u"Uploaded: '{}' ==> '{}'".format(os.path.basename(path), gav))
        else:
            print(u"Couldn't upload the file.")

def main():
    """
    Main function of the CLI
    """

    parser,args = get_args()

    conn = ArtifactTool(args.mvn_url, args.mvn_user, args.mvn_password)

    if args.download and args.upload:
        raise ValueError(u"It's impossible to download and upload artifacts simultaneously.")

    if args.delete and (args.download or args.upload):
        raise ValueError(u"It's impossible to delete and download/upload artifacts simultaneously.")

    if args.download:
        conn.download_artifact(args.gav, args.path, args.download_repo, args.filename)
    elif args.upload:
        conn.upload_artifact(args.gav, args.path, args.upload_repo, args.no_check_exist)
    elif args.delete:
        conn.delete_artifact(args.gav, args.upload_repo)
    elif args.info:
        conn.get_info(args.gav, args.download_repo)
    else:
        parser.print_help()

        
if __name__ == '__main__':
    main()
