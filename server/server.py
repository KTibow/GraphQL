"""Server for GraphQL and frontend."""
from sanic import Sanic, response
from schema import schema

app = Sanic(__name__)


@app.route("/", methods=["POST"])
async def graphql(request):
    """Handle GraphQL requests.

    Args:
        request: The request object.

    Returns:
        The response object.
    """
    graphql_response = schema.execute(request.json["query"])
    if graphql_response.errors:
        print(graphql_response.errors)
        return response.json(
            {"errors": [str(error) for error in graphql_response.errors]}, status=400
        )
    return response.json({"data": graphql_response.data})


@app.route("/")
async def index(_request):
    """Return the home page.

    Returns:
        The response object.
    """
    return await response.file("frontend/index.html", mime_type="text/html")


@app.route("/wiki")
async def item_wiki(_request):
    """Return the wiki page for an item.

    Returns:
        The response object.
    """
    return await response.file("frontend/wiki.html", mime_type="text/html")


@app.route("/graphiql")
async def graphiql(_request):
    """Return the GraphiQL interface.

    Returns:
        The response object.
    """
    return await response.file("frontend/graphiql.html", mime_type="text/html")


@app.route("/site.css")
async def site_css(_request):
    """Return the CSS for the site.

    Returns:
        The response object.
    """
    return await response.file("frontend/site.css", mime_type="text/css")


app.run(host="0.0.0.0")
