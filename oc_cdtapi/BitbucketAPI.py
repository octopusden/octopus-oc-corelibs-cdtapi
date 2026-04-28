import logging
import os
import posixpath

from . import API


class BitbucketAPIError(API.HttpAPIError):
    pass


class BitbucketAPI(API.HttpAPI):
    """
    Bitbucket API implementation
    """
    
    # This automatically allows usage of BITBUCKET_* environment variables
    _env_prefix = 'BITBUCKET'
    _error = BitbucketAPIError
    
    # Default timeout for all HTTP requests (in seconds)
    DEFAULT_TIMEOUT = 30
    
    def __init__(self, *args, **argv):
        """
        Initialize the parent class with username/password authentication
        The parent class HttpAPI already handles reading BITBUCKET_USER and BITBUCKET_PASSWORD
        from environment variables and sets up basic authentication
        """
        super().__init__(*args, **argv)
        
        # No need for bearer token headers - basic auth is handled by parent class
        # But we can add content-type header for JSON requests
        self.headers = {"Content-Type": "application/json"}
    
    def __req(self, req):
        """
        Join a URL to one posixpath-compatible string
        :param req: request, may be list of str
        :return str: joined req
        """
        if not req:
            return req
        
        if isinstance(req, list):
            logging.log(5, "re-formatting requested list [%s] URL to string" % ', '.join(req))
            req = posixpath.sep.join(req)
        
        return req
    
    def re(self, req):
        """
        Re-define default request formatter, not to be called directly
        This forms request URL separated by slash from string array
        :param req: list of str or str for sub-url
        :return str: full joined URL
        """
        if not req:
            return self.root
        
        # Form URL: {root}/rest/api/1.0/{req}
        return posixpath.join(self.root, "rest", "api", "1.0", self.__req(req))
    
    def get_repo(self, project, repo_slug):
        """
        Get repository information
        :param str project: project key
        :param str repo_slug: repository slug
        :return dict: repository information
        """
        logging.debug('Reached %s.get_repo', self.__class__.__name__)
        logging.debug('project: {0}'.format(project))
        logging.debug('repo_slug: {0}'.format(repo_slug))
        
        req = ['projects', project, 'repos', repo_slug]
        
        response = self.get(req, headers=self.headers, timeout=self.DEFAULT_TIMEOUT)
        repo_data = response.json()
        
        logging.debug('Retrieved repository: %s', repo_data.get('name', 'unknown'))
        
        return repo_data
    
    def create_repo(self, project, repo_name, description=None, forkable=True, public=False):
        """
        Create a new repository
        :param str project: project key
        :param str repo_name: repository name
        :param str description: repository description (optional)
        :param bool forkable: whether the repository is forkable
        :param bool public: whether the repository is public
        :return dict: created repository information
        """
        logging.debug('Reached %s.create_repo', self.__class__.__name__)
        logging.debug('project: {0}'.format(project))
        logging.debug('repo_name: {0}'.format(repo_name))
        
        req = ['projects', project, 'repos']
        
        data = {
            'name': repo_name,
            'forkable': forkable,
            'public': public
        }
        
        if description:
            data['description'] = description
        
        response = self.post(req, json=data, headers=self.headers, timeout=self.DEFAULT_TIMEOUT)
        repo_data = response.json()
        
        logging.debug('Created repository with slug: %s', repo_data.get('slug', 'unknown'))
        
        return repo_data
    
    def archive_repo(self, project, repo_slug):
        """
        Archive a repository
        :param str project: project key
        :param str repo_slug: repository slug
        :return dict: archived repository information
        """
        logging.debug('Reached %s.archive_repo', self.__class__.__name__)
        logging.debug('project: {0}'.format(project))
        logging.debug('repo_slug: {0}'.format(repo_slug))
        
        req = ['projects', project, 'repos', repo_slug]
        
        # Archive by updating the archived flag
        data = {'archived': True}
        
        response = self.put(req, json=data, headers=self.headers, timeout=self.DEFAULT_TIMEOUT)
        repo_data = response.json()
        
        logging.debug('Archived repository: %s', repo_data.get('name', 'unknown'))
        
        return repo_data
    
    def get_repos(self, project):
        """
        Get list of repositories for a project
        :param str project: project key
        :return list: repositories
        """
        logging.debug('Reached %s.get_repos', self.__class__.__name__)
        logging.debug('project: {0}'.format(project))
        
        req = ['projects', project, 'repos']
        
        response = self.get(req, headers=self.headers, timeout=self.DEFAULT_TIMEOUT)
        repos_data = response.json()
        
        repos = repos_data.get('values', [])
        
        logging.debug('About to return an array of %d elements', len(repos))
        
        return repos
    
    def delete_repo(self, project, repo_slug):
        """
        Delete a repository
        :param str project: project key
        :param str repo_slug: repository slug
        :return requests.Response: server response
        """
        logging.debug('Reached %s.delete_repo', self.__class__.__name__)
        logging.debug('project: {0}'.format(project))
        logging.debug('repo_slug: {0}'.format(repo_slug))
        
        req = ['projects', project, 'repos', repo_slug]
        
        response = self.delete(req, headers=self.headers, timeout=self.DEFAULT_TIMEOUT)
        
        logging.debug('Deleted repository: %s', repo_slug)
        
        return response
    
    def get_branches(self, project, repo_slug):
        """
        Get list of branches for a repository
        :param str project: project key
        :param str repo_slug: repository slug
        :return list: branches
        """
        logging.debug('Reached %s.get_branches', self.__class__.__name__)
        logging.debug('project: {0}'.format(project))
        logging.debug('repo_slug: {0}'.format(repo_slug))
        
        req = ['projects', project, 'repos', repo_slug, 'branches']
        
        response = self.get(req, headers=self.headers, timeout=self.DEFAULT_TIMEOUT)
        branches_data = response.json()
        
        branches = branches_data.get('values', [])
        
        logging.debug('About to return an array of %d elements', len(branches))
        
        return branches
    
    def ping_bitbucket(self):
        """
        Send a request to Bitbucket root to check connectivity
        :return: server response
        """
        logging.debug('Reached %s.ping_bitbucket', self.__class__.__name__)
        
        return self.get([], headers=self.headers, timeout=self.DEFAULT_TIMEOUT).content