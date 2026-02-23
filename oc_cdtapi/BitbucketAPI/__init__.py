# coding: utf-8

# flake8: noqa

"""
    bitbucket-server-api

    <h1>REST Resources Provided By: Bitbucket Server - REST</h1> <p>     This is the reference document for the Atlassian Bitbucket REST API. The REST API is for developers who want to: </p> <ul>     <li>integrate Bitbucket with other applications;</li>     <li>create scripts that interact with Bitbucket; or</li>     <li>develop plugins that enhance the Bitbucket UI, using REST to interact with the backend.</li> </ul> You can read more about developing Bitbucket plugins in the <a href=\"https://developer.atlassian.com/server/bitbucket/\">Bitbucket Developer Documentation</a>. <p></p> <h2 id=\"gettingstarted\">Getting started</h2> <p>     Because the REST API is based on open standards, you can use any web development language or command line tool     capable of generating an HTTP request to access the API. See the     <a href=\"https://developer.atlassian.com/server/bitbucket/reference/rest-api/\">developer documentation</a> for a     basic     usage example. </p> <p>     If you're already working with the     <a href=\"https://developer.atlassian.com/server/framework/atlassian-sdk/\">Atlassian SDK</a>,     the <a href=\"https://developer.atlassian.com/server/framework/atlassian-sdk/using-the-rest-api-browser/\">REST API         Browser</a> is a great tool for exploring and experimenting with the Bitbucket REST API. </p> <h2>     <a name=\"StructureoftheRESTURIs\"></a>Structure of the REST URIs</h2> <p>     Bitbucket's REST APIs provide access to resources (data entities) via URI paths. To use a REST API, your application     will     make an HTTP request and parse the response. The Bitbucket REST API uses JSON as its communication format, and the     standard     HTTP methods like GET, PUT, POST and DELETE. URIs for Bitbucket's REST API resource have the following structure: </p> <pre>    http://host:port/context/rest/api-name/api-version/path/to/resource </pre> <p>     For example, the following URI would retrieve a page of the latest commits to the <strong>jira</strong> repository     in     the <strong>Jira</strong> project on <a href=\"https://stash.atlassian.com\">https://stash.atlassian.com</a>. </p> <pre>    https://stash.atlassian.com/rest/api/1.0/projects/JIRA/repos/jira/commits </pre> <p>     See the API descriptions below for a full list of available resources. </p> <p>     Alternatively we also publish a list of resources in     <a href=\"http://en.wikipedia.org/wiki/Web_Application_Description_Language\">WADL</a> format. It is available     <a href=\"bitbucket-rest.wadl\">here</a>. </p> <h2 id=\"paging-params\">Paged APIs</h2> <p>     Bitbucket uses paging to conserve server resources and limit response size for resources that return potentially     large     collections of items. A request to a paged API will result in a <code>values</code> array wrapped in a JSON object     with some paging metadata, like this: </p> <pre>    {         \"size\": 3,         \"limit\": 3,         \"isLastPage\": false,         \"values\": [             { /* result 0 */ },             { /* result 1 */ },             { /* result 2 */ }         ],         \"start\": 0,         \"filter\": null,         \"nextPageStart\": 3     } </pre> <p>     Clients can use the <code>limit</code> and <code>start</code> query parameters to retrieve the desired number of     results. </p> <p>     The <code>limit</code> parameter indicates how many results to return per page. Most APIs default to returning     <code>25</code> if the limit is left unspecified. This number can be increased, but note that a resource-specific     hard limit will apply. These hard limits can be configured by server administrators, so it's always best practice to     check the <code>limit</code> attribute on the response to see what limit has been applied.     The request to get a larger page should look like this: </p> <pre>    http://host:port/context/rest/api-name/api-version/path/to/resource?limit={desired size of page} </pre> <p>     For example: </p> <pre>    https://stash.atlassian.com/rest/api/1.0/projects/JIRA/repos/jira/commits?limit=1000 </pre> <p>     The <code>start</code> parameter indicates which item should be used as the first item in the page of results. All     paged responses contain an <code>isLastPage</code> attribute indicating whether another page of items exists. </p> <p><strong>Important:</strong> If more than one page exists (i.e. the response contains     <code>\"isLastPage\": false</code>), the response object will also contain a <code>nextPageStart</code> attribute     which <strong><em>must</em></strong> be used by the client as the <code>start</code> parameter on the next request.     Identifiers of adjacent objects in a page may not be contiguous, so the start of the next page is <em>not</em>     necessarily the start of the last page plus the last page's size. A client should always use     <code>nextPageStart</code> to avoid unexpected results from a paged API.     The request to get a subsequent page should look like this: </p> <pre>    http://host:port/context/rest/api-name/api-version/path/to/resource?start={nextPageStart from previous response} </pre> <p>     For example: </p> <pre>    https://stash.atlassian.com/rest/api/1.0/projects/JIRA/repos/jira/commits?start=25 </pre> <h2 id=\"authentication\">Authentication</h2> <p>     Any authentication that works against Bitbucket will work against the REST API. <b>The preferred authentication         methods         are HTTP Basic (when using SSL) and OAuth</b>. Other supported methods include: HTTP Cookies and Trusted     Applications. </p> <p>     You can find OAuth code samples in several programming languages at     <a         href=\"https://bitbucket.org/atlassian_tutorial/atlassian-oauth-examples\">bitbucket.org/atlassian_tutorial/atlassian-oauth-examples</a>. </p> <p>     The log-in page uses cookie-based authentication, so if you are using Bitbucket in a browser you can call REST from     JavaScript on the page and rely on the authentication that the browser has established. </p> <h2 id=\"errors-and-validation\">Errors &amp; Validation</h2> <p>     If a request fails due to client error, the resource will return an HTTP response code in the 40x range. These can     be broadly categorised into: </p> <table>     <tbody>         <tr>             <th>HTTP Code</th>             <th>Description</th>         </tr>         <tr>             <td>400 (Bad Request)</td>             <td>                 One or more of the required parameters or attributes:                 <ul>                     <li>were missing from the request;</li>                     <li>incorrectly formatted; or</li>                     <li>inappropriate in the given context.</li>                 </ul>             </td>         </tr>         <tr>             <td>401 (Unauthorized)</td>             <td>                 Either:                 <ul>                     <li>Authentication is required but was not attempted.</li>                     <li>Authentication was attempted but failed.</li>                     <li>Authentication was successful but the authenticated user does not have the requisite permission                         for the resource.</li>                 </ul>                 See the individual resource documentation for details of required permissions.             </td>         </tr>         <tr>             <td>403 (Forbidden)</td>             <td>                 Actions are usually \"forbidden\" if they involve breaching the licensed user limit of the server, or                 degrading the authenticated user's permission level. See the individual resource documentation for more                 details.             </td>         </tr>         <tr>             <td>404 (Not Found)</td>             <td>                 The entity you are attempting to access, or the project or repository containing it, does not exist.             </td>         </tr>         <tr>             <td>405 (Method Not Allowed)</td>             <td>                 The request HTTP method is not appropriate for the targeted resource. For example an HTTP GET to a                 resource that only accepts an HTTP POST will result in a 405.             </td>         </tr>         <tr>             <td>409 (Conflict)</td>             <td>                 The attempted update failed due to some conflict with an existing resource. For example:                 <ul>                     <li>Creating a project with a key that already exists</li>                     <li>Merging an out-of-date pull request</li>                     <li>Deleting a comment that has replies</li>                     <li>etc.</li>                 </ul>                 See the individual resource documentation for more details.             </td>         </tr>         <tr>             <td>415 (Unsupported Media Type)</td>             <td>                 The request entity has a <code>Content-Type</code> that the server does not support. Almost all of the                 Bitbucket REST API accepts <code>application/json</code> format, but check the individual resource                 documentation for more details. Additionally, double-check that you are setting the                 <code>Content-Type</code> header correctly on your request (e.g. using                 <code>-H \"Content-Type: application/json\"</code> in cURL).             </td>         </tr>     </tbody> </table> <p>     For <strong>400</strong> HTTP codes the response will typically contain one or more validation error messages,     for example: </p> <pre>    {         \"errors\": [             {                 \"context\": \"name\",                 \"message\": \"The name should be between 1 and 255 characters.\",                 \"exceptionName\": null             },             {                 \"context\": \"email\",                 \"message\": \"The email should be a valid email address.\",                 \"exceptionName\": null             }         ]     }     </pre> <p>     The <code>context</code> attribute indicates which parameter or request entity attribute failed validation. Note     that the <code>context</code> may be null. </p> <p>     For <strong>401</strong>, <strong>403</strong>, <strong>404</strong> and <strong>409</strong>     HTTP codes, the response will contain one or more descriptive error messages: </p> <pre>    {         \"errors\": [             {                 \"context\": null,                 \"message\": \"A detailed error message.\",                 \"exceptionName\": null             }         ]     }     </pre> <p>     A <strong>500</strong> (Server Error) HTTP code indicates an incorrect resource url or an unexpected server error.     Double-check the URL you are trying to access, then report the issue to your server administrator or     <a href=\"https://support.atlassian.com/\">Atlassian Support</a> if problems persist. </p> <h2 id=\"personal-repositories\">Personal Repositories</h2> <p>     Bitbucket allows users to manage their own repositories, called personal repositories. These are repositories     associated     with the user and to which they always have REPO_ADMIN permission. </p> <p>     Accessing personal repositories via REST is achieved through the normal project-centric REST URLs     using the user's slug prefixed by tilde as the project key. E.g. to list personal repositories for a     user with slug \"johnsmith\" you would make a GET to: </p> <pre>http://example.com/rest/api/1.0/projects/~johnsmith/repos</pre> <p></p> <p>     In addition to this, Bitbucket allows access to these repositories through an alternate set of user-centric REST     URLs     beginning with: </p> <pre>http://example.com/rest/api/1.0/users/~{userSlug}/repos</pre> E.g. to list the forks of the repository with slug \"nodejs\" in the personal project of user with slug \"johnsmith\" using the regular REST URL you would make a GET to: <pre>http://example.com/rest/api/1.0/projects/~johnsmith/repos/nodejs/forks</pre> Using the alternate URL, you would make a GET to: <pre>http://example.com/rest/api/1.0/users/johnsmith/repos/nodejs/forks</pre> <p></p>

    The version of the OpenAPI document: 7.3.1
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


__version__ = "1.0.0"

# Define package exports
__all__ = [
    "BranchesApi",
    "BuildStatusApi",
    "CommitsApi",
    "PostWebhookApi",
    "ProjectsApi",
    "PullRequestsApi",
    "RepositoriesApi",
    "WebhookApi",
    "ApiResponse",
    "ApiClient",
    "Configuration",
    "OpenApiException",
    "ApiTypeError",
    "ApiValueError",
    "ApiKeyError",
    "ApiAttributeError",
    "ApiException",
    "Branch",
    "BranchMetadata",
    "BranchMetadataAheadBehind",
    "BranchMetadataBuildStatus",
    "BranchMetadataJiraIssue",
    "BranchMetadataOutgoingPullRequest",
    "BranchMetadataOutgoingPullRequestOneOf",
    "BranchMetadataOutgoingPullRequestOneOf1",
    "BranchesPage",
    "BuildStatus",
    "BuildStatusPage",
    "Children",
    "ChildrenAllOfValues",
    "Commit",
    "CommitParentsInner",
    "CommitsPage",
    "CreateBranch",
    "CreateRepository",
    "DefaultBranch",
    "DeleteBranch",
    "Directory",
    "Errors",
    "ErrorsErrorsInner",
    "File",
    "FileLinesInner",
    "FileOrDirectory",
    "Link",
    "Page",
    "Path",
    "PostWebhook",
    "Project",
    "ProjectLinks",
    "ProjectsPage",
    "PullRequest",
    "PullRequestDelete",
    "PullRequestState",
    "PullRequestUpdate",
    "PullRequestsPage",
    "RepositoriesPage",
    "Repository",
    "RepositoryLinks",
    "RepositoryRef",
    "RepositoryRefRepository",
    "RepositoryRefRepositoryProject",
    "User",
    "UserRole",
    "Webhook",
    "WebhookConfiguration",
    "WebhookEvent",
    "WebhooksPage",
]

# import apis into sdk package
from .api.branches_api import BranchesApi as BranchesApi
from .api.build_status_api import BuildStatusApi as BuildStatusApi
from .api.commits_api import CommitsApi as CommitsApi
from .api.post_webhook_api import PostWebhookApi as PostWebhookApi
from .api.projects_api import ProjectsApi as ProjectsApi
from .api.pull_requests_api import PullRequestsApi as PullRequestsApi
from .api.repositories_api import RepositoriesApi as RepositoriesApi
from .api.webhook_api import WebhookApi as WebhookApi

# import ApiClient
from .api_response import ApiResponse as ApiResponse
from .api_client import ApiClient as ApiClient
from .configuration import Configuration as Configuration
from .exceptions import OpenApiException as OpenApiException
from .exceptions import ApiTypeError as ApiTypeError
from .exceptions import ApiValueError as ApiValueError
from .exceptions import ApiKeyError as ApiKeyError
from .exceptions import ApiAttributeError as ApiAttributeError
from .exceptions import ApiException as ApiException

# import models into sdk package
from .models.branch import Branch as Branch
from .models.branch_metadata import BranchMetadata as BranchMetadata
from .models.branch_metadata_ahead_behind import BranchMetadataAheadBehind as BranchMetadataAheadBehind
from .models.branch_metadata_build_status import BranchMetadataBuildStatus as BranchMetadataBuildStatus
from .models.branch_metadata_jira_issue import BranchMetadataJiraIssue as BranchMetadataJiraIssue
from .models.branch_metadata_outgoing_pull_request import BranchMetadataOutgoingPullRequest as BranchMetadataOutgoingPullRequest
from .models.branch_metadata_outgoing_pull_request_one_of import BranchMetadataOutgoingPullRequestOneOf as BranchMetadataOutgoingPullRequestOneOf
from .models.branch_metadata_outgoing_pull_request_one_of1 import BranchMetadataOutgoingPullRequestOneOf1 as BranchMetadataOutgoingPullRequestOneOf1
from .models.branches_page import BranchesPage as BranchesPage
from .models.build_status import BuildStatus as BuildStatus
from .models.build_status_page import BuildStatusPage as BuildStatusPage
from .models.children import Children as Children
from .models.children_all_of_values import ChildrenAllOfValues as ChildrenAllOfValues
from .models.commit import Commit as Commit
from .models.commit_parents_inner import CommitParentsInner as CommitParentsInner
from .models.commits_page import CommitsPage as CommitsPage
from .models.create_branch import CreateBranch as CreateBranch
from .models.create_repository import CreateRepository as CreateRepository
from .models.default_branch import DefaultBranch as DefaultBranch
from .models.delete_branch import DeleteBranch as DeleteBranch
from .models.directory import Directory as Directory
from .models.errors import Errors as Errors
from .models.errors_errors_inner import ErrorsErrorsInner as ErrorsErrorsInner
from .models.file import File as File
from .models.file_lines_inner import FileLinesInner as FileLinesInner
from .models.file_or_directory import FileOrDirectory as FileOrDirectory
from .models.link import Link as Link
from .models.page import Page as Page
from .models.path import Path as Path
from .models.post_webhook import PostWebhook as PostWebhook
from .models.project import Project as Project
from .models.project_links import ProjectLinks as ProjectLinks
from .models.projects_page import ProjectsPage as ProjectsPage
from .models.pull_request import PullRequest as PullRequest
from .models.pull_request_delete import PullRequestDelete as PullRequestDelete
from .models.pull_request_state import PullRequestState as PullRequestState
from .models.pull_request_update import PullRequestUpdate as PullRequestUpdate
from .models.pull_requests_page import PullRequestsPage as PullRequestsPage
from .models.repositories_page import RepositoriesPage as RepositoriesPage
from .models.repository import Repository as Repository
from .models.repository_links import RepositoryLinks as RepositoryLinks
from .models.repository_ref import RepositoryRef as RepositoryRef
from .models.repository_ref_repository import RepositoryRefRepository as RepositoryRefRepository
from .models.repository_ref_repository_project import RepositoryRefRepositoryProject as RepositoryRefRepositoryProject
from .models.user import User as User
from .models.user_role import UserRole as UserRole
from .models.webhook import Webhook as Webhook
from .models.webhook_configuration import WebhookConfiguration as WebhookConfiguration
from .models.webhook_event import WebhookEvent as WebhookEvent
from .models.webhooks_page import WebhooksPage as WebhooksPage

