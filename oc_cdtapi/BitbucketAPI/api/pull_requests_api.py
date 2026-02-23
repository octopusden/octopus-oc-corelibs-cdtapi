"""
    bitbucket-server-api

    <h1>REST Resources Provided By: Bitbucket Server - REST</h1> <p>     This is the reference document for the Atlassian Bitbucket REST API. The REST API is for developers who want to: </p> <ul>     <li>integrate Bitbucket with other applications;</li>     <li>create scripts that interact with Bitbucket; or</li>     <li>develop plugins that enhance the Bitbucket UI, using REST to interact with the backend.</li> </ul> You can read more about developing Bitbucket plugins in the <a href=\"https://developer.atlassian.com/server/bitbucket/\">Bitbucket Developer Documentation</a>. <p></p> <h2 id=\"gettingstarted\">Getting started</h2> <p>     Because the REST API is based on open standards, you can use any web development language or command line tool     capable of generating an HTTP request to access the API. See the     <a href=\"https://developer.atlassian.com/server/bitbucket/reference/rest-api/\">developer documentation</a> for a     basic     usage example. </p> <p>     If you're already working with the     <a href=\"https://developer.atlassian.com/server/framework/atlassian-sdk/\">Atlassian SDK</a>,     the <a href=\"https://developer.atlassian.com/server/framework/atlassian-sdk/using-the-rest-api-browser/\">REST API         Browser</a> is a great tool for exploring and experimenting with the Bitbucket REST API. </p> <h2>     <a name=\"StructureoftheRESTURIs\"></a>Structure of the REST URIs</h2> <p>     Bitbucket's REST APIs provide access to resources (data entities) via URI paths. To use a REST API, your application     will     make an HTTP request and parse the response. The Bitbucket REST API uses JSON as its communication format, and the     standard     HTTP methods like GET, PUT, POST and DELETE. URIs for Bitbucket's REST API resource have the following structure: </p> <pre>    http://host:port/context/rest/api-name/api-version/path/to/resource </pre> <p>     For example, the following URI would retrieve a page of the latest commits to the <strong>jira</strong> repository     in     the <strong>Jira</strong> project on <a href=\"https://stash.atlassian.com\">https://stash.atlassian.com</a>. </p> <pre>    https://stash.atlassian.com/rest/api/1.0/projects/JIRA/repos/jira/commits </pre> <p>     See the API descriptions below for a full list of available resources. </p> <p>     Alternatively we also publish a list of resources in     <a href=\"http://en.wikipedia.org/wiki/Web_Application_Description_Language\">WADL</a> format. It is available     <a href=\"bitbucket-rest.wadl\">here</a>. </p> <h2 id=\"paging-params\">Paged APIs</h2> <p>     Bitbucket uses paging to conserve server resources and limit response size for resources that return potentially     large     collections of items. A request to a paged API will result in a <code>values</code> array wrapped in a JSON object     with some paging metadata, like this: </p> <pre>    {         \"size\": 3,         \"limit\": 3,         \"isLastPage\": false,         \"values\": [             { /* result 0 */ },             { /* result 1 */ },             { /* result 2 */ }         ],         \"start\": 0,         \"filter\": null,         \"nextPageStart\": 3     } </pre> <p>     Clients can use the <code>limit</code> and <code>start</code> query parameters to retrieve the desired number of     results. </p> <p>     The <code>limit</code> parameter indicates how many results to return per page. Most APIs default to returning     <code>25</code> if the limit is left unspecified. This number can be increased, but note that a resource-specific     hard limit will apply. These hard limits can be configured by server administrators, so it's always best practice to     check the <code>limit</code> attribute on the response to see what limit has been applied.     The request to get a larger page should look like this: </p> <pre>    http://host:port/context/rest/api-name/api-version/path/to/resource?limit={desired size of page} </pre> <p>     For example: </p> <pre>    https://stash.atlassian.com/rest/api/1.0/projects/JIRA/repos/jira/commits?limit=1000 </pre> <p>     The <code>start</code> parameter indicates which item should be used as the first item in the page of results. All     paged responses contain an <code>isLastPage</code> attribute indicating whether another page of items exists. </p> <p><strong>Important:</strong> If more than one page exists (i.e. the response contains     <code>\"isLastPage\": false</code>), the response object will also contain a <code>nextPageStart</code> attribute     which <strong><em>must</em></strong> be used by the client as the <code>start</code> parameter on the next request.     Identifiers of adjacent objects in a page may not be contiguous, so the start of the next page is <em>not</em>     necessarily the start of the last page plus the last page's size. A client should always use     <code>nextPageStart</code> to avoid unexpected results from a paged API.     The request to get a subsequent page should look like this: </p> <pre>    http://host:port/context/rest/api-name/api-version/path/to/resource?start={nextPageStart from previous response} </pre> <p>     For example: </p> <pre>    https://stash.atlassian.com/rest/api/1.0/projects/JIRA/repos/jira/commits?start=25 </pre> <h2 id=\"authentication\">Authentication</h2> <p>     Any authentication that works against Bitbucket will work against the REST API. <b>The preferred authentication         methods         are HTTP Basic (when using SSL) and OAuth</b>. Other supported methods include: HTTP Cookies and Trusted     Applications. </p> <p>     You can find OAuth code samples in several programming languages at     <a         href=\"https://bitbucket.org/atlassian_tutorial/atlassian-oauth-examples\">bitbucket.org/atlassian_tutorial/atlassian-oauth-examples</a>. </p> <p>     The log-in page uses cookie-based authentication, so if you are using Bitbucket in a browser you can call REST from     JavaScript on the page and rely on the authentication that the browser has established. </p> <h2 id=\"errors-and-validation\">Errors &amp; Validation</h2> <p>     If a request fails due to client error, the resource will return an HTTP response code in the 40x range. These can     be broadly categorised into: </p> <table>     <tbody>         <tr>             <th>HTTP Code</th>             <th>Description</th>         </tr>         <tr>             <td>400 (Bad Request)</td>             <td>                 One or more of the required parameters or attributes:                 <ul>                     <li>were missing from the request;</li>                     <li>incorrectly formatted; or</li>                     <li>inappropriate in the given context.</li>                 </ul>             </td>         </tr>         <tr>             <td>401 (Unauthorized)</td>             <td>                 Either:                 <ul>                     <li>Authentication is required but was not attempted.</li>                     <li>Authentication was attempted but failed.</li>                     <li>Authentication was successful but the authenticated user does not have the requisite permission                         for the resource.</li>                 </ul>                 See the individual resource documentation for details of required permissions.             </td>         </tr>         <tr>             <td>403 (Forbidden)</td>             <td>                 Actions are usually \"forbidden\" if they involve breaching the licensed user limit of the server, or                 degrading the authenticated user's permission level. See the individual resource documentation for more                 details.             </td>         </tr>         <tr>             <td>404 (Not Found)</td>             <td>                 The entity you are attempting to access, or the project or repository containing it, does not exist.             </td>         </tr>         <tr>             <td>405 (Method Not Allowed)</td>             <td>                 The request HTTP method is not appropriate for the targeted resource. For example an HTTP GET to a                 resource that only accepts an HTTP POST will result in a 405.             </td>         </tr>         <tr>             <td>409 (Conflict)</td>             <td>                 The attempted update failed due to some conflict with an existing resource. For example:                 <ul>                     <li>Creating a project with a key that already exists</li>                     <li>Merging an out-of-date pull request</li>                     <li>Deleting a comment that has replies</li>                     <li>etc.</li>                 </ul>                 See the individual resource documentation for more details.             </td>         </tr>         <tr>             <td>415 (Unsupported Media Type)</td>             <td>                 The request entity has a <code>Content-Type</code> that the server does not support. Almost all of the                 Bitbucket REST API accepts <code>application/json</code> format, but check the individual resource                 documentation for more details. Additionally, double-check that you are setting the                 <code>Content-Type</code> header correctly on your request (e.g. using                 <code>-H \"Content-Type: application/json\"</code> in cURL).             </td>         </tr>     </tbody> </table> <p>     For <strong>400</strong> HTTP codes the response will typically contain one or more validation error messages,     for example: </p> <pre>    {         \"errors\": [             {                 \"context\": \"name\",                 \"message\": \"The name should be between 1 and 255 characters.\",                 \"exceptionName\": null             },             {                 \"context\": \"email\",                 \"message\": \"The email should be a valid email address.\",                 \"exceptionName\": null             }         ]     }     </pre> <p>     The <code>context</code> attribute indicates which parameter or request entity attribute failed validation. Note     that the <code>context</code> may be null. </p> <p>     For <strong>401</strong>, <strong>403</strong>, <strong>404</strong> and <strong>409</strong>     HTTP codes, the response will contain one or more descriptive error messages: </p> <pre>    {         \"errors\": [             {                 \"context\": null,                 \"message\": \"A detailed error message.\",                 \"exceptionName\": null             }         ]     }     </pre> <p>     A <strong>500</strong> (Server Error) HTTP code indicates an incorrect resource url or an unexpected server error.     Double-check the URL you are trying to access, then report the issue to your server administrator or     <a href=\"https://support.atlassian.com/\">Atlassian Support</a> if problems persist. </p> <h2 id=\"personal-repositories\">Personal Repositories</h2> <p>     Bitbucket allows users to manage their own repositories, called personal repositories. These are repositories     associated     with the user and to which they always have REPO_ADMIN permission. </p> <p>     Accessing personal repositories via REST is achieved through the normal project-centric REST URLs     using the user's slug prefixed by tilde as the project key. E.g. to list personal repositories for a     user with slug \"johnsmith\" you would make a GET to: </p> <pre>http://example.com/rest/api/1.0/projects/~johnsmith/repos</pre> <p></p> <p>     In addition to this, Bitbucket allows access to these repositories through an alternate set of user-centric REST     URLs     beginning with: </p> <pre>http://example.com/rest/api/1.0/users/~{userSlug}/repos</pre> E.g. to list the forks of the repository with slug \"nodejs\" in the personal project of user with slug \"johnsmith\" using the regular REST URL you would make a GET to: <pre>http://example.com/rest/api/1.0/projects/~johnsmith/repos/nodejs/forks</pre> Using the alternate URL, you would make a GET to: <pre>http://example.com/rest/api/1.0/users/johnsmith/repos/nodejs/forks</pre> <p></p>

    The version of the OpenAPI document: 7.3.1
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import warnings
from pydantic import validate_call, Field, StrictFloat, StrictStr, StrictInt
from typing import Any, Dict, List, Optional, Tuple, Union
from typing_extensions import Annotated

from pydantic import Field, StrictInt, StrictStr, field_validator
from typing import List, Optional
from typing_extensions import Annotated
from oc_cdtapi.BitbucketAPI.models.pull_request import PullRequest
from oc_cdtapi.BitbucketAPI.models.pull_request_delete import PullRequestDelete
from oc_cdtapi.BitbucketAPI.models.pull_request_update import PullRequestUpdate
from oc_cdtapi.BitbucketAPI.models.pull_requests_page import PullRequestsPage
from oc_cdtapi.BitbucketAPI.models.user import User

from oc_cdtapi.BitbucketAPI.api_client import ApiClient, RequestSerialized
from oc_cdtapi.BitbucketAPI.api_response import ApiResponse
from oc_cdtapi.BitbucketAPI.rest import RESTResponseType


class PullRequestsApi:
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None) -> None:
        if api_client is None:
            api_client = ApiClient.get_default()
        self.api_client = api_client


    @validate_call
    def create_pull_request(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request: Optional[PullRequest] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> PullRequest:
        """Create Pull Request

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Create a new pull request between two branches. The branches may be in the same repository, or different ones. When using different repositories, they must still be in the same {@link Repository#getHierarchyId() hierarchy}.  The authenticated user must have REPO_READ permission for the \"from\" and \"to\"repositories to call this resource.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request:
        :type pull_request: PullRequest
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._create_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request=pull_request,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '201': "PullRequest",
            '400': "Errors",
            '401': "Errors",
            '404': "Errors",
            '409': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data


    @validate_call
    def create_pull_request_with_http_info(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request: Optional[PullRequest] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[PullRequest]:
        """Create Pull Request

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Create a new pull request between two branches. The branches may be in the same repository, or different ones. When using different repositories, they must still be in the same {@link Repository#getHierarchyId() hierarchy}.  The authenticated user must have REPO_READ permission for the \"from\" and \"to\"repositories to call this resource.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request:
        :type pull_request: PullRequest
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._create_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request=pull_request,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '201': "PullRequest",
            '400': "Errors",
            '401': "Errors",
            '404': "Errors",
            '409': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )


    @validate_call
    def create_pull_request_without_preload_content(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request: Optional[PullRequest] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Create Pull Request

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Create a new pull request between two branches. The branches may be in the same repository, or different ones. When using different repositories, they must still be in the same {@link Repository#getHierarchyId() hierarchy}.  The authenticated user must have REPO_READ permission for the \"from\" and \"to\"repositories to call this resource.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request:
        :type pull_request: PullRequest
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._create_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request=pull_request,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '201': "PullRequest",
            '400': "Errors",
            '401': "Errors",
            '404': "Errors",
            '409': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        return response_data.response


    def _create_pull_request_serialize(
        self,
        project_key,
        repository_slug,
        pull_request,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {
        }

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[
            str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]
        ] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        if project_key is not None:
            _path_params['projectKey'] = project_key
        if repository_slug is not None:
            _path_params['repositorySlug'] = repository_slug
        # process the query parameters
        # process the header parameters
        # process the form parameters
        # process the body parameter
        if pull_request is not None:
            _body_params = pull_request


        # set the HTTP header `Accept`
        if 'Accept' not in _header_params:
            _header_params['Accept'] = self.api_client.select_header_accept(
                [
                    'application/json'
                ]
            )

        # set the HTTP header `Content-Type`
        if _content_type:
            _header_params['Content-Type'] = _content_type
        else:
            _default_content_type = (
                self.api_client.select_header_content_type(
                    [
                        'application/json'
                    ]
                )
            )
            if _default_content_type is not None:
                _header_params['Content-Type'] = _default_content_type

        # authentication setting
        _auth_settings: List[str] = [
        ]

        return self.api_client.param_serialize(
            method='POST',
            resource_path='/rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )




    @validate_call
    def delete_pull_request(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        pull_request_delete: Optional[PullRequestDelete] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> None:
        """Delete pull request

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Deletes a pull request.  To call this resource, users must be authenticated and have permission to view the pull request. Additionally, they must:  be the pull request author, if the system is configured to allow authors to delete their own pull requests (this is the default) OR have repository administrator permission for the repository the pull request is targeting A body containing the version of the pull request must be provided with this request.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param pull_request_delete:
        :type pull_request_delete: PullRequestDelete
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._delete_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            pull_request_delete=pull_request_delete,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '204': None,
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data


    @validate_call
    def delete_pull_request_with_http_info(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        pull_request_delete: Optional[PullRequestDelete] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[None]:
        """Delete pull request

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Deletes a pull request.  To call this resource, users must be authenticated and have permission to view the pull request. Additionally, they must:  be the pull request author, if the system is configured to allow authors to delete their own pull requests (this is the default) OR have repository administrator permission for the repository the pull request is targeting A body containing the version of the pull request must be provided with this request.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param pull_request_delete:
        :type pull_request_delete: PullRequestDelete
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._delete_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            pull_request_delete=pull_request_delete,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '204': None,
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )


    @validate_call
    def delete_pull_request_without_preload_content(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        pull_request_delete: Optional[PullRequestDelete] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Delete pull request

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Deletes a pull request.  To call this resource, users must be authenticated and have permission to view the pull request. Additionally, they must:  be the pull request author, if the system is configured to allow authors to delete their own pull requests (this is the default) OR have repository administrator permission for the repository the pull request is targeting A body containing the version of the pull request must be provided with this request.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param pull_request_delete:
        :type pull_request_delete: PullRequestDelete
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._delete_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            pull_request_delete=pull_request_delete,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '204': None,
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        return response_data.response


    def _delete_pull_request_serialize(
        self,
        project_key,
        repository_slug,
        pull_request_id,
        pull_request_delete,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {
        }

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[
            str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]
        ] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        if project_key is not None:
            _path_params['projectKey'] = project_key
        if repository_slug is not None:
            _path_params['repositorySlug'] = repository_slug
        if pull_request_id is not None:
            _path_params['pullRequestId'] = pull_request_id
        # process the query parameters
        # process the header parameters
        # process the form parameters
        # process the body parameter
        if pull_request_delete is not None:
            _body_params = pull_request_delete


        # set the HTTP header `Accept`
        if 'Accept' not in _header_params:
            _header_params['Accept'] = self.api_client.select_header_accept(
                [
                    'application/json'
                ]
            )

        # set the HTTP header `Content-Type`
        if _content_type:
            _header_params['Content-Type'] = _content_type
        else:
            _default_content_type = (
                self.api_client.select_header_content_type(
                    [
                        'application/json'
                    ]
                )
            )
            if _default_content_type is not None:
                _header_params['Content-Type'] = _default_content_type

        # authentication setting
        _auth_settings: List[str] = [
        ]

        return self.api_client.param_serialize(
            method='DELETE',
            resource_path='/rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )




    @validate_call
    def get_default_reviewers(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        source_repo_id: Annotated[StrictInt, Field(description="The ID of the repository in which the source ref exists")],
        target_repo_id: Annotated[StrictInt, Field(description="The ID of the repository in which the target ref exists")],
        source_ref_id: Annotated[StrictStr, Field(description="The ID of the source ref")],
        target_ref_id: Annotated[Optional[StrictStr], Field(description="The ID of the target ref ")] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> List[User]:
        """Get default reviewers

        Return a set of users who are required reviewers for pull requests created from the given source repository and ref to the given target ref in this repository.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param source_repo_id: The ID of the repository in which the source ref exists (required)
        :type source_repo_id: int
        :param target_repo_id: The ID of the repository in which the target ref exists (required)
        :type target_repo_id: int
        :param source_ref_id: The ID of the source ref (required)
        :type source_ref_id: str
        :param target_ref_id: The ID of the target ref 
        :type target_ref_id: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_default_reviewers_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id,
            source_ref_id=source_ref_id,
            target_ref_id=target_ref_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "List[User]",
            '400': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data


    @validate_call
    def get_default_reviewers_with_http_info(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        source_repo_id: Annotated[StrictInt, Field(description="The ID of the repository in which the source ref exists")],
        target_repo_id: Annotated[StrictInt, Field(description="The ID of the repository in which the target ref exists")],
        source_ref_id: Annotated[StrictStr, Field(description="The ID of the source ref")],
        target_ref_id: Annotated[Optional[StrictStr], Field(description="The ID of the target ref ")] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[List[User]]:
        """Get default reviewers

        Return a set of users who are required reviewers for pull requests created from the given source repository and ref to the given target ref in this repository.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param source_repo_id: The ID of the repository in which the source ref exists (required)
        :type source_repo_id: int
        :param target_repo_id: The ID of the repository in which the target ref exists (required)
        :type target_repo_id: int
        :param source_ref_id: The ID of the source ref (required)
        :type source_ref_id: str
        :param target_ref_id: The ID of the target ref 
        :type target_ref_id: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_default_reviewers_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id,
            source_ref_id=source_ref_id,
            target_ref_id=target_ref_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "List[User]",
            '400': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )


    @validate_call
    def get_default_reviewers_without_preload_content(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        source_repo_id: Annotated[StrictInt, Field(description="The ID of the repository in which the source ref exists")],
        target_repo_id: Annotated[StrictInt, Field(description="The ID of the repository in which the target ref exists")],
        source_ref_id: Annotated[StrictStr, Field(description="The ID of the source ref")],
        target_ref_id: Annotated[Optional[StrictStr], Field(description="The ID of the target ref ")] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Get default reviewers

        Return a set of users who are required reviewers for pull requests created from the given source repository and ref to the given target ref in this repository.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param source_repo_id: The ID of the repository in which the source ref exists (required)
        :type source_repo_id: int
        :param target_repo_id: The ID of the repository in which the target ref exists (required)
        :type target_repo_id: int
        :param source_ref_id: The ID of the source ref (required)
        :type source_ref_id: str
        :param target_ref_id: The ID of the target ref 
        :type target_ref_id: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_default_reviewers_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            source_repo_id=source_repo_id,
            target_repo_id=target_repo_id,
            source_ref_id=source_ref_id,
            target_ref_id=target_ref_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "List[User]",
            '400': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        return response_data.response


    def _get_default_reviewers_serialize(
        self,
        project_key,
        repository_slug,
        source_repo_id,
        target_repo_id,
        source_ref_id,
        target_ref_id,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {
        }

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[
            str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]
        ] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        if project_key is not None:
            _path_params['projectKey'] = project_key
        if repository_slug is not None:
            _path_params['repositorySlug'] = repository_slug
        # process the query parameters
        if source_repo_id is not None:
            
            _query_params.append(('sourceRepoId', source_repo_id))
            
        if target_repo_id is not None:
            
            _query_params.append(('targetRepoId', target_repo_id))
            
        if source_ref_id is not None:
            
            _query_params.append(('sourceRefId', source_ref_id))
            
        if target_ref_id is not None:
            
            _query_params.append(('targetRefId', target_ref_id))
            
        # process the header parameters
        # process the form parameters
        # process the body parameter


        # set the HTTP header `Accept`
        if 'Accept' not in _header_params:
            _header_params['Accept'] = self.api_client.select_header_accept(
                [
                    'application/json'
                ]
            )


        # authentication setting
        _auth_settings: List[str] = [
        ]

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/rest/default-reviewers/1.0/projects/{projectKey}/repos/{repositorySlug}/reviewers',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )




    @validate_call
    def get_diff(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        context_lines: Annotated[Optional[StrictInt], Field(description="the number of context lines to include around added/removed lines in the diff")] = None,
        whitespaces: Annotated[Optional[StrictStr], Field(description="optional whitespace flag which can be set to ignore-all")] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> str:
        """Get PR Diff

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Streams the raw diff for a pull request.  The authenticated user must have REPO_READ permission for the repository that this pull request targets to call this resource.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param context_lines: the number of context lines to include around added/removed lines in the diff
        :type context_lines: int
        :param whitespaces: optional whitespace flag which can be set to ignore-all
        :type whitespaces: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_diff_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            context_lines=context_lines,
            whitespaces=whitespaces,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "str",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data


    @validate_call
    def get_diff_with_http_info(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        context_lines: Annotated[Optional[StrictInt], Field(description="the number of context lines to include around added/removed lines in the diff")] = None,
        whitespaces: Annotated[Optional[StrictStr], Field(description="optional whitespace flag which can be set to ignore-all")] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[str]:
        """Get PR Diff

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Streams the raw diff for a pull request.  The authenticated user must have REPO_READ permission for the repository that this pull request targets to call this resource.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param context_lines: the number of context lines to include around added/removed lines in the diff
        :type context_lines: int
        :param whitespaces: optional whitespace flag which can be set to ignore-all
        :type whitespaces: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_diff_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            context_lines=context_lines,
            whitespaces=whitespaces,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "str",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )


    @validate_call
    def get_diff_without_preload_content(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        context_lines: Annotated[Optional[StrictInt], Field(description="the number of context lines to include around added/removed lines in the diff")] = None,
        whitespaces: Annotated[Optional[StrictStr], Field(description="optional whitespace flag which can be set to ignore-all")] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Get PR Diff

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Streams the raw diff for a pull request.  The authenticated user must have REPO_READ permission for the repository that this pull request targets to call this resource.

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param context_lines: the number of context lines to include around added/removed lines in the diff
        :type context_lines: int
        :param whitespaces: optional whitespace flag which can be set to ignore-all
        :type whitespaces: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_diff_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            context_lines=context_lines,
            whitespaces=whitespaces,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "str",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        return response_data.response


    def _get_diff_serialize(
        self,
        project_key,
        repository_slug,
        pull_request_id,
        context_lines,
        whitespaces,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {
        }

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[
            str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]
        ] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        if project_key is not None:
            _path_params['projectKey'] = project_key
        if repository_slug is not None:
            _path_params['repositorySlug'] = repository_slug
        if pull_request_id is not None:
            _path_params['pullRequestId'] = pull_request_id
        # process the query parameters
        if context_lines is not None:
            
            _query_params.append(('contextLines', context_lines))
            
        if whitespaces is not None:
            
            _query_params.append(('whitespaces', whitespaces))
            
        # process the header parameters
        # process the form parameters
        # process the body parameter


        # set the HTTP header `Accept`
        if 'Accept' not in _header_params:
            _header_params['Accept'] = self.api_client.select_header_accept(
                [
                    'text/plain', 
                    'application/json'
                ]
            )


        # authentication setting
        _auth_settings: List[str] = [
        ]

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}.diff',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )




    @validate_call
    def get_pull_request(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> PullRequest:
        """Get pull request

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Retrieve a pull request.  The authenticated user must have REPO_READ permission for the repository that this pull request targets to call this resource. 

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "PullRequest",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data


    @validate_call
    def get_pull_request_with_http_info(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[PullRequest]:
        """Get pull request

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Retrieve a pull request.  The authenticated user must have REPO_READ permission for the repository that this pull request targets to call this resource. 

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "PullRequest",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )


    @validate_call
    def get_pull_request_without_preload_content(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Get pull request

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Retrieve a pull request.  The authenticated user must have REPO_READ permission for the repository that this pull request targets to call this resource. 

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "PullRequest",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        return response_data.response


    def _get_pull_request_serialize(
        self,
        project_key,
        repository_slug,
        pull_request_id,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {
        }

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[
            str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]
        ] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        if project_key is not None:
            _path_params['projectKey'] = project_key
        if repository_slug is not None:
            _path_params['repositorySlug'] = repository_slug
        if pull_request_id is not None:
            _path_params['pullRequestId'] = pull_request_id
        # process the query parameters
        # process the header parameters
        # process the form parameters
        # process the body parameter


        # set the HTTP header `Accept`
        if 'Accept' not in _header_params:
            _header_params['Accept'] = self.api_client.select_header_accept(
                [
                    'application/json'
                ]
            )


        # authentication setting
        _auth_settings: List[str] = [
        ]

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )




    @validate_call
    def get_pull_requests_paged(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        limit: Optional[StrictInt] = None,
        start: Optional[StrictInt] = None,
        state: Annotated[Optional[StrictStr], Field(description="(optional, defaults to OPEN). Supply ALL to return pull request in any state. If a state is supplied only pull requests in the specified state will be returned. Either OPEN, DECLINED or MERGED")] = None,
        order: Annotated[Optional[StrictStr], Field(description="(optional, defaults to NEWEST) the order to return pull requests in, either OLDEST (as in: \"oldest first\") or NEWEST.")] = None,
        at: Annotated[Optional[StrictStr], Field(description="(optional) a fully-qualified branch ID to find pull requests to or from, such as refs/heads/master")] = None,
        direction: Annotated[Optional[StrictStr], Field(description="(optional, defaults to INCOMING) the direction relative to the specified repository. Either INCOMING or OUTGOING.")] = None,
        filter_text: Annotated[Optional[StrictStr], Field(description="(optional) If specified, only pull requests where the title or description contains the supplied string will be returned.")] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> PullRequestsPage:
        """Get Pull Request Page

        Retrieve a page of pull requests to or from the specified repository.  The authenticated user must have REPO_READ permission for the specified repository to call this resource. Optionally clients can specify PR participant filters. Each filter has a mandatory username.N parameter, and the optional role.N and approved.N parameters.  username.N - the \"root\" of a single participant filter, where \"N\" is a natural number starting from 1. This allows clients to specify multiple participant filters, by providing consecutive filters as username.1, username.2 etc. Note that the filters numbering has to start with 1 and be continuous for all filters to be processed. The total allowed number of participant filters is 10 and all filters exceeding that limit will be dropped. role.N(optional) the role associated with username.N. This must be one of AUTHOR, REVIEWER, orPARTICIPANT approved.N(optional) the approved status associated with username.N. That is whether username.N has approved the PR. Either true, or false

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param limit:
        :type limit: int
        :param start:
        :type start: int
        :param state: (optional, defaults to OPEN). Supply ALL to return pull request in any state. If a state is supplied only pull requests in the specified state will be returned. Either OPEN, DECLINED or MERGED
        :type state: str
        :param order: (optional, defaults to NEWEST) the order to return pull requests in, either OLDEST (as in: \"oldest first\") or NEWEST.
        :type order: str
        :param at: (optional) a fully-qualified branch ID to find pull requests to or from, such as refs/heads/master
        :type at: str
        :param direction: (optional, defaults to INCOMING) the direction relative to the specified repository. Either INCOMING or OUTGOING.
        :type direction: str
        :param filter_text: (optional) If specified, only pull requests where the title or description contains the supplied string will be returned.
        :type filter_text: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_pull_requests_paged_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            limit=limit,
            start=start,
            state=state,
            order=order,
            at=at,
            direction=direction,
            filter_text=filter_text,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "PullRequestsPage",
            '400': "Errors",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data


    @validate_call
    def get_pull_requests_paged_with_http_info(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        limit: Optional[StrictInt] = None,
        start: Optional[StrictInt] = None,
        state: Annotated[Optional[StrictStr], Field(description="(optional, defaults to OPEN). Supply ALL to return pull request in any state. If a state is supplied only pull requests in the specified state will be returned. Either OPEN, DECLINED or MERGED")] = None,
        order: Annotated[Optional[StrictStr], Field(description="(optional, defaults to NEWEST) the order to return pull requests in, either OLDEST (as in: \"oldest first\") or NEWEST.")] = None,
        at: Annotated[Optional[StrictStr], Field(description="(optional) a fully-qualified branch ID to find pull requests to or from, such as refs/heads/master")] = None,
        direction: Annotated[Optional[StrictStr], Field(description="(optional, defaults to INCOMING) the direction relative to the specified repository. Either INCOMING or OUTGOING.")] = None,
        filter_text: Annotated[Optional[StrictStr], Field(description="(optional) If specified, only pull requests where the title or description contains the supplied string will be returned.")] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[PullRequestsPage]:
        """Get Pull Request Page

        Retrieve a page of pull requests to or from the specified repository.  The authenticated user must have REPO_READ permission for the specified repository to call this resource. Optionally clients can specify PR participant filters. Each filter has a mandatory username.N parameter, and the optional role.N and approved.N parameters.  username.N - the \"root\" of a single participant filter, where \"N\" is a natural number starting from 1. This allows clients to specify multiple participant filters, by providing consecutive filters as username.1, username.2 etc. Note that the filters numbering has to start with 1 and be continuous for all filters to be processed. The total allowed number of participant filters is 10 and all filters exceeding that limit will be dropped. role.N(optional) the role associated with username.N. This must be one of AUTHOR, REVIEWER, orPARTICIPANT approved.N(optional) the approved status associated with username.N. That is whether username.N has approved the PR. Either true, or false

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param limit:
        :type limit: int
        :param start:
        :type start: int
        :param state: (optional, defaults to OPEN). Supply ALL to return pull request in any state. If a state is supplied only pull requests in the specified state will be returned. Either OPEN, DECLINED or MERGED
        :type state: str
        :param order: (optional, defaults to NEWEST) the order to return pull requests in, either OLDEST (as in: \"oldest first\") or NEWEST.
        :type order: str
        :param at: (optional) a fully-qualified branch ID to find pull requests to or from, such as refs/heads/master
        :type at: str
        :param direction: (optional, defaults to INCOMING) the direction relative to the specified repository. Either INCOMING or OUTGOING.
        :type direction: str
        :param filter_text: (optional) If specified, only pull requests where the title or description contains the supplied string will be returned.
        :type filter_text: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_pull_requests_paged_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            limit=limit,
            start=start,
            state=state,
            order=order,
            at=at,
            direction=direction,
            filter_text=filter_text,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "PullRequestsPage",
            '400': "Errors",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )


    @validate_call
    def get_pull_requests_paged_without_preload_content(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        limit: Optional[StrictInt] = None,
        start: Optional[StrictInt] = None,
        state: Annotated[Optional[StrictStr], Field(description="(optional, defaults to OPEN). Supply ALL to return pull request in any state. If a state is supplied only pull requests in the specified state will be returned. Either OPEN, DECLINED or MERGED")] = None,
        order: Annotated[Optional[StrictStr], Field(description="(optional, defaults to NEWEST) the order to return pull requests in, either OLDEST (as in: \"oldest first\") or NEWEST.")] = None,
        at: Annotated[Optional[StrictStr], Field(description="(optional) a fully-qualified branch ID to find pull requests to or from, such as refs/heads/master")] = None,
        direction: Annotated[Optional[StrictStr], Field(description="(optional, defaults to INCOMING) the direction relative to the specified repository. Either INCOMING or OUTGOING.")] = None,
        filter_text: Annotated[Optional[StrictStr], Field(description="(optional) If specified, only pull requests where the title or description contains the supplied string will be returned.")] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Get Pull Request Page

        Retrieve a page of pull requests to or from the specified repository.  The authenticated user must have REPO_READ permission for the specified repository to call this resource. Optionally clients can specify PR participant filters. Each filter has a mandatory username.N parameter, and the optional role.N and approved.N parameters.  username.N - the \"root\" of a single participant filter, where \"N\" is a natural number starting from 1. This allows clients to specify multiple participant filters, by providing consecutive filters as username.1, username.2 etc. Note that the filters numbering has to start with 1 and be continuous for all filters to be processed. The total allowed number of participant filters is 10 and all filters exceeding that limit will be dropped. role.N(optional) the role associated with username.N. This must be one of AUTHOR, REVIEWER, orPARTICIPANT approved.N(optional) the approved status associated with username.N. That is whether username.N has approved the PR. Either true, or false

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param limit:
        :type limit: int
        :param start:
        :type start: int
        :param state: (optional, defaults to OPEN). Supply ALL to return pull request in any state. If a state is supplied only pull requests in the specified state will be returned. Either OPEN, DECLINED or MERGED
        :type state: str
        :param order: (optional, defaults to NEWEST) the order to return pull requests in, either OLDEST (as in: \"oldest first\") or NEWEST.
        :type order: str
        :param at: (optional) a fully-qualified branch ID to find pull requests to or from, such as refs/heads/master
        :type at: str
        :param direction: (optional, defaults to INCOMING) the direction relative to the specified repository. Either INCOMING or OUTGOING.
        :type direction: str
        :param filter_text: (optional) If specified, only pull requests where the title or description contains the supplied string will be returned.
        :type filter_text: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_pull_requests_paged_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            limit=limit,
            start=start,
            state=state,
            order=order,
            at=at,
            direction=direction,
            filter_text=filter_text,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "PullRequestsPage",
            '400': "Errors",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        return response_data.response


    def _get_pull_requests_paged_serialize(
        self,
        project_key,
        repository_slug,
        limit,
        start,
        state,
        order,
        at,
        direction,
        filter_text,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {
        }

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[
            str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]
        ] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        if project_key is not None:
            _path_params['projectKey'] = project_key
        if repository_slug is not None:
            _path_params['repositorySlug'] = repository_slug
        # process the query parameters
        if limit is not None:
            
            _query_params.append(('limit', limit))
            
        if start is not None:
            
            _query_params.append(('start', start))
            
        if state is not None:
            
            _query_params.append(('state', state))
            
        if order is not None:
            
            _query_params.append(('order', order))
            
        if at is not None:
            
            _query_params.append(('at', at))
            
        if direction is not None:
            
            _query_params.append(('direction', direction))
            
        if filter_text is not None:
            
            _query_params.append(('filterText', filter_text))
            
        # process the header parameters
        # process the form parameters
        # process the body parameter


        # set the HTTP header `Accept`
        if 'Accept' not in _header_params:
            _header_params['Accept'] = self.api_client.select_header_accept(
                [
                    'application/json'
                ]
            )


        # authentication setting
        _auth_settings: List[str] = [
        ]

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )




    @validate_call
    def get_rest_api1_0_projects_project_key_repos_repository_slug_pull_requests_pull_request_id_patch(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> str:
        """Get PR Patch

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Streams a patch representing a pull request.  The authenticated user must have REPO_READ permission for the repository that this pull request targets to call this resource. 

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_rest_api1_0_projects_project_key_repos_repository_slug_pull_requests_pull_request_id_patch_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "str",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data


    @validate_call
    def get_rest_api1_0_projects_project_key_repos_repository_slug_pull_requests_pull_request_id_patch_with_http_info(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[str]:
        """Get PR Patch

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Streams a patch representing a pull request.  The authenticated user must have REPO_READ permission for the repository that this pull request targets to call this resource. 

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_rest_api1_0_projects_project_key_repos_repository_slug_pull_requests_pull_request_id_patch_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "str",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )


    @validate_call
    def get_rest_api1_0_projects_project_key_repos_repository_slug_pull_requests_pull_request_id_patch_without_preload_content(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictStr,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Get PR Patch

        This API can also be invoked via a user-centric URL when addressing repositories in personal projects.  Streams a patch representing a pull request.  The authenticated user must have REPO_READ permission for the repository that this pull request targets to call this resource. 

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._get_rest_api1_0_projects_project_key_repos_repository_slug_pull_requests_pull_request_id_patch_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "str",
            '401': "Errors",
            '404': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        return response_data.response


    def _get_rest_api1_0_projects_project_key_repos_repository_slug_pull_requests_pull_request_id_patch_serialize(
        self,
        project_key,
        repository_slug,
        pull_request_id,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {
        }

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[
            str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]
        ] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        if project_key is not None:
            _path_params['projectKey'] = project_key
        if repository_slug is not None:
            _path_params['repositorySlug'] = repository_slug
        if pull_request_id is not None:
            _path_params['pullRequestId'] = pull_request_id
        # process the query parameters
        # process the header parameters
        # process the form parameters
        # process the body parameter


        # set the HTTP header `Accept`
        if 'Accept' not in _header_params:
            _header_params['Accept'] = self.api_client.select_header_accept(
                [
                    'text/plain', 
                    'application/json'
                ]
            )


        # authentication setting
        _auth_settings: List[str] = [
        ]

        return self.api_client.param_serialize(
            method='GET',
            resource_path='/rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}.patch',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )




    @validate_call
    def update_pull_request(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        pull_request_update: Optional[PullRequestUpdate] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> PullRequest:
        """Update pull request

        Update the title, description, reviewers or destination branch of an existing pull request.  Note: the reviewers list may be updated using this resource. However the author and participants list may not.  The authenticated user must either: * be the author of the pull request and have the REPO_READ permission for the repository that this pull request targets; or * have the REPO_WRITE permission for the repository that this pull request targets to call this resource. 

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param pull_request_update:
        :type pull_request_update: PullRequestUpdate
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._update_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            pull_request_update=pull_request_update,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "PullRequest",
            '400': "Errors",
            '401': "Errors",
            '404': "Errors",
            '409': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data


    @validate_call
    def update_pull_request_with_http_info(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        pull_request_update: Optional[PullRequestUpdate] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> ApiResponse[PullRequest]:
        """Update pull request

        Update the title, description, reviewers or destination branch of an existing pull request.  Note: the reviewers list may be updated using this resource. However the author and participants list may not.  The authenticated user must either: * be the author of the pull request and have the REPO_READ permission for the repository that this pull request targets; or * have the REPO_WRITE permission for the repository that this pull request targets to call this resource. 

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param pull_request_update:
        :type pull_request_update: PullRequestUpdate
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._update_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            pull_request_update=pull_request_update,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "PullRequest",
            '400': "Errors",
            '401': "Errors",
            '404': "Errors",
            '409': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        response_data.read()
        return self.api_client.response_deserialize(
            response_data=response_data,
            response_types_map=_response_types_map,
        )


    @validate_call
    def update_pull_request_without_preload_content(
        self,
        project_key: StrictStr,
        repository_slug: StrictStr,
        pull_request_id: StrictInt,
        pull_request_update: Optional[PullRequestUpdate] = None,
        _request_timeout: Union[
            None,
            Annotated[StrictFloat, Field(gt=0)],
            Tuple[
                Annotated[StrictFloat, Field(gt=0)],
                Annotated[StrictFloat, Field(gt=0)]
            ]
        ] = None,
        _request_auth: Optional[Dict[StrictStr, Any]] = None,
        _content_type: Optional[StrictStr] = None,
        _headers: Optional[Dict[StrictStr, Any]] = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> RESTResponseType:
        """Update pull request

        Update the title, description, reviewers or destination branch of an existing pull request.  Note: the reviewers list may be updated using this resource. However the author and participants list may not.  The authenticated user must either: * be the author of the pull request and have the REPO_READ permission for the repository that this pull request targets; or * have the REPO_WRITE permission for the repository that this pull request targets to call this resource. 

        :param project_key: (required)
        :type project_key: str
        :param repository_slug: (required)
        :type repository_slug: str
        :param pull_request_id: (required)
        :type pull_request_id: int
        :param pull_request_update:
        :type pull_request_update: PullRequestUpdate
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """ # noqa: E501

        _param = self._update_pull_request_serialize(
            project_key=project_key,
            repository_slug=repository_slug,
            pull_request_id=pull_request_id,
            pull_request_update=pull_request_update,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index
        )

        _response_types_map: Dict[str, Optional[str]] = {
            '200': "PullRequest",
            '400': "Errors",
            '401': "Errors",
            '404': "Errors",
            '409': "Errors",
        }
        response_data = self.api_client.call_api(
            *_param,
            _request_timeout=_request_timeout
        )
        return response_data.response


    def _update_pull_request_serialize(
        self,
        project_key,
        repository_slug,
        pull_request_id,
        pull_request_update,
        _request_auth,
        _content_type,
        _headers,
        _host_index,
    ) -> RequestSerialized:

        _host = None

        _collection_formats: Dict[str, str] = {
        }

        _path_params: Dict[str, str] = {}
        _query_params: List[Tuple[str, str]] = []
        _header_params: Dict[str, Optional[str]] = _headers or {}
        _form_params: List[Tuple[str, str]] = []
        _files: Dict[
            str, Union[str, bytes, List[str], List[bytes], List[Tuple[str, bytes]]]
        ] = {}
        _body_params: Optional[bytes] = None

        # process the path parameters
        if project_key is not None:
            _path_params['projectKey'] = project_key
        if repository_slug is not None:
            _path_params['repositorySlug'] = repository_slug
        if pull_request_id is not None:
            _path_params['pullRequestId'] = pull_request_id
        # process the query parameters
        # process the header parameters
        # process the form parameters
        # process the body parameter
        if pull_request_update is not None:
            _body_params = pull_request_update


        # set the HTTP header `Accept`
        if 'Accept' not in _header_params:
            _header_params['Accept'] = self.api_client.select_header_accept(
                [
                    'application/json'
                ]
            )

        # set the HTTP header `Content-Type`
        if _content_type:
            _header_params['Content-Type'] = _content_type
        else:
            _default_content_type = (
                self.api_client.select_header_content_type(
                    [
                        'application/json'
                    ]
                )
            )
            if _default_content_type is not None:
                _header_params['Content-Type'] = _default_content_type

        # authentication setting
        _auth_settings: List[str] = [
        ]

        return self.api_client.param_serialize(
            method='PUT',
            resource_path='/rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}',
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth
        )


