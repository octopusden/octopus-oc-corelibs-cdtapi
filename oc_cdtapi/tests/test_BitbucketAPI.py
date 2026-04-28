import logging
import os
import re
import unittest

from unittest.mock import patch


from ..BitbucketAPI import BitbucketAPI

import json


class FakeJson(object):
    def __init__(self):
        self.response = None

    def setresp(self, resp):
        self.response = resp

    def json(self):
        return self.response


class _Response(object):
    """
    Fake response object
    """

    def __init__(self, data):
        self.content = data
        self.status_code = 200

    def json(self):
        return json.loads(self.content)


class _Session(object):
    """
    Fake requests session
    """

    def __init__(self, handler):
        self.handler = handler
        self.auth = None

    def get(self, req, params=None, **other):
        return _Response(self.handler(req, 'GET'))

    def post(self, req, params=None, json=None, **other):
        return _Response(self.handler(req, 'POST', json))

    def put(self, req, params=None, json=None, **other):
        return _Response(self.handler(req, 'PUT', json))

    def delete(self, req, params=None, **other):
        return _Response(self.handler(req, 'DELETE'))


class _BitbucketAPI(BitbucketAPI):

    def __init__(self, *args, **argv):
        super(_BitbucketAPI, self).__init__(*args, **argv)
        self.web = _Session(self._read_url)

    def _read_url(self, url, method='GET', data=None):
        """
        Override http request method to return fake responses
        """
        # GET /rest/api/1.0/projects/PROJ/repos/my-repo
        if re.match('.+\/projects\/.+\/repos\/[^\/]+$', url) and method == 'GET':
            return json.dumps({
                "slug": "my-repo",
                "id": 1,
                "name": "My Repository",
                "description": "Test repository",
                "state": "AVAILABLE",
                "forkable": True,
                "public": False,
                "project": {
                    "key": "PROJ",
                    "name": "Project"
                }
            })
        
        # POST /rest/api/1.0/projects/PROJ/repos (create repo)
        elif re.match('.+\/projects\/.+\/repos$', url) and method == 'POST':
            repo_name = data.get('name', 'new-repo') if data else 'new-repo'
            return json.dumps({
                "slug": repo_name.lower().replace(' ', '-'),
                "id": 2,
                "name": repo_name,
                "description": data.get('description', '') if data else '',
                "state": "AVAILABLE",
                "forkable": data.get('forkable', True) if data else True,
                "public": data.get('public', False) if data else False,
                "project": {
                    "key": "PROJ",
                    "name": "Project"
                }
            })
        
        # PUT /rest/api/1.0/projects/PROJ/repos/my-repo (archive repo)
        elif re.match('.+\/projects\/.+\/repos\/[^\/]+$', url) and method == 'PUT':
            return json.dumps({
                "slug": "my-repo",
                "id": 1,
                "name": "My Repository",
                "description": "Test repository",
                "state": "AVAILABLE",
                "archived": True,
                "forkable": True,
                "public": False,
                "project": {
                    "key": "PROJ",
                    "name": "Project"
                }
            })
        
        # GET /rest/api/1.0/projects/PROJ/repos (list repos)
        elif re.match('.+\/projects\/.+\/repos$', url) and method == 'GET':
            return json.dumps({
                "size": 2,
                "limit": 25,
                "isLastPage": True,
                "values": [
                    {
                        "slug": "repo-1",
                        "id": 1,
                        "name": "Repository 1",
                        "state": "AVAILABLE"
                    },
                    {
                        "slug": "repo-2",
                        "id": 2,
                        "name": "Repository 2",
                        "state": "AVAILABLE"
                    }
                ]
            })
        
        # DELETE /rest/api/1.0/projects/PROJ/repos/my-repo
        elif re.match('.+\/projects\/.+\/repos\/[^\/]+$', url) and method == 'DELETE':
            return json.dumps({})
        
        # GET /rest/api/1.0/projects/PROJ/repos/my-repo/branches
        elif re.match('.+\/projects\/.+\/repos\/.+\/branches$', url) and method == 'GET':
            return json.dumps({
                "size": 2,
                "limit": 25,
                "isLastPage": True,
                "values": [
                    {
                        "id": "refs/heads/main",
                        "displayId": "main",
                        "type": "BRANCH",
                        "isDefault": True
                    },
                    {
                        "id": "refs/heads/develop",
                        "displayId": "develop",
                        "type": "BRANCH",
                        "isDefault": False
                    }
                ]
            })
        
        # Default fallback
        raise AssertionError("Unexpected mocked request: {} {}".format(method, url))


class TestBitbucketAPI(unittest.TestCase):

    @patch.dict(os.environ, {
        "BITBUCKET_URL": "https://bitbucket.example.com",
        "BITBUCKET_USER": "testuser",
        "BITBUCKET_PASSWORD": "testpass"
    })
    def setUp(self):
        self.bitbucket_api = _BitbucketAPI()

    def test_re(self):
        """Test URL request formation"""
        self.assertEqual(
            "https://bitbucket.example.com/rest/api/1.0/test",
            self.bitbucket_api.re("test")
        )
        self.assertEqual(
            "https://bitbucket.example.com/rest/api/1.0/test/test",
            self.bitbucket_api.re("test/test")
        )
        self.assertEqual(
            "https://bitbucket.example.com/rest/api/1.0/test/test",
            self.bitbucket_api.re(["test", "test"])
        )

    def test_get_repo(self):
        """Test getting repository information"""
        repo = self.bitbucket_api.get_repo('PROJ', 'my-repo')
        
        self.assertEqual(repo['slug'], 'my-repo')
        self.assertEqual(repo['name'], 'My Repository')
        self.assertEqual(repo['state'], 'AVAILABLE')
        self.assertEqual(repo['project']['key'], 'PROJ')

    def test_create_repo(self):
        """Test creating a new repository"""
        repo = self.bitbucket_api.create_repo(
            'PROJ',
            'New Repository',
            description='A new test repository',
            forkable=True,
            public=False
        )
        
        self.assertEqual(repo['slug'], 'new-repository')
        self.assertEqual(repo['name'], 'New Repository')
        self.assertEqual(repo['description'], 'A new test repository')
        self.assertTrue(repo['forkable'])
        self.assertFalse(repo['public'])

    def test_create_repo_minimal(self):
        """Test creating a repository with minimal parameters"""
        repo = self.bitbucket_api.create_repo('PROJ', 'Simple Repo')
        
        self.assertEqual(repo['slug'], 'simple-repo')
        self.assertEqual(repo['name'], 'Simple Repo')
        self.assertTrue(repo['forkable'])
        self.assertFalse(repo['public'])

    def test_archive_repo(self):
        """Test archiving a repository"""
        repo = self.bitbucket_api.archive_repo('PROJ', 'my-repo')
        
        self.assertEqual(repo['slug'], 'my-repo')
        self.assertTrue(repo['archived'])

    def test_get_repos(self):
        """Test getting list of repositories"""
        repos = self.bitbucket_api.get_repos('PROJ')
        
        self.assertEqual(len(repos), 2)
        self.assertEqual(repos[0]['slug'], 'repo-1')
        self.assertEqual(repos[1]['slug'], 'repo-2')

    def test_delete_repo(self):
        """Test deleting a repository"""
        response = self.bitbucket_api.delete_repo('PROJ', 'my-repo')
        
        self.assertEqual(response.status_code, 200)

    def test_get_branches(self):
        """Test getting list of branches"""
        branches = self.bitbucket_api.get_branches('PROJ', 'my-repo')
        
        self.assertEqual(len(branches), 2)
        self.assertEqual(branches[0]['displayId'], 'main')
        self.assertTrue(branches[0]['isDefault'])
        self.assertEqual(branches[1]['displayId'], 'develop')
        self.assertFalse(branches[1]['isDefault'])

if __name__ == '__main__':
    unittest.main()