from sanic import Sanic, response

from schema import schema

app = Sanic()


@app.route("/", methods=["POST"])
async def graphql(request):
    result = schema.execute(request.json["query"])
    if result.errors:
        return response.json(
            {"errors": [str(error) for error in result.errors]}, status=400
        )
    else:
        return response.json(result.data)


@app.route("/")
async def index(request):
    return response.html(open("frontend/index.html").read())
    """    fetch("/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: "{ hello }"
            })
        }).then(function(response) {
            return response.json()
        }).then(function(json) {
            console.log(json)
        })"""


@app.route("/site.css")
async def site_css(request):
    return await response.file("frontend/site.css", mime_type="text/css")


app.run(host="0.0.0.0")
