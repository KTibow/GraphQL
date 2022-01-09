from sanic import Sanic, response
from schema import schema

app = Sanic(__name__)


@app.route("/", methods=["POST"])
async def graphql(request):
    result = schema.execute(request.json["query"])
    if result.errors:
        print(result.errors[0])
        return response.json(
            {"errors": [str(error) for error in result.errors]}, status=400
        )
    else:
        return response.json({"data": result.data})


@app.route("/")
async def index(request):
    return response.html(open("frontend/index.html").read())


@app.route("/wiki")
async def item_wiki(request):
    return response.html(open("frontend/wiki.html").read())


@app.route("/graphiql")
async def graphiql(request):
    return response.html(open("frontend/graphiql.html").read())


@app.route("/site.css")
async def site_css(request):
    return await response.file("frontend/site.css", mime_type="text/css")


app.run(host="0.0.0.0")
