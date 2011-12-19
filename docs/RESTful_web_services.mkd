
REST basics
-----------

REST (Representational State Transfer) is a term coined by Roy Fielding in
[his Ph.D. Thesis of 2000](http://www.ics.uci.edu/~fielding/pubs/dissertation/top.htm).
It is an architectural style, not a precise protocol or interface.

The REST architectural style is based on the fundamental technologies of
the web:

1. Resources: The data and/or software on the server that you wish to
   interact with.
2. URIs (Uniform Resource Identifiers), which actually almost always are
   URLs (Uniform Resource Locators): The links or addresses of the web.
3. Representations: The specific formats for request and response data.
4. HTTP (HyperText Transfer Protocol): The rules for how clients should
   talk with servers to manage sending requests and obtaining responses.

One of the most important points of a RESTful web service is that it
uses HTTP the way it is supposed to: Every single request/response cycle
is independent of each other; the protocol is stateless.
