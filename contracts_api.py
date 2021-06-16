from flask import Flask
from flask_restful import Api, Resource, abort
from flask_pymongo import PyMongo
import json
import os
import requests

app = Flask(__name__)
api = Api(app)
app.config["MONGO_URI"] = "mongodb://localhost:27017/contracts"
mongo = PyMongo(app)


API_KEY = "KATYXDXN2WD5PHEK4M51ZBE2277S4IGJT3"

def tryGetSourceEtherscan(contractAddr):
    # get Sourcecode API
    url = "https://api.etherscan.io/api?module=contract&action=getsourcecode&address="+contractAddr+"&apikey="+API_KEY
    r = requests.get(url)
    data = json.loads(r.text)
    return data['result'][0]['SourceCode']

def formatJSONFile(jsonFile):
    f = open(jsonFile, "r")
    fileData = f.read()[1:-1]
    i = fileData.find("{")
    fileData = fileData[i:]
    return fileData

class contracts(Resource):
    def get(self, contractAddr):
        myquery = { "contractAddr":contractAddr }
        contractAnalysis = mongo.db.analysis.find_one(myquery, {"_id":0})
        if contractAnalysis is None:
            sourcecode = tryGetSourceEtherscan(contractAddr)
            if len(sourcecode) > 0:
                os.system("python ./honeybadger/honeybadger.py -j -ru https://etherscan.io/address/"+contractAddr)
                fileData = formatJSONFile("results/"+contractAddr+".json")
                mongo.db.analysis.insert(json.loads(fileData))
                return json.loads(fileData)
            else:
                return abort("Contract Address not found...")
        return contractAnalysis

api.add_resource(contracts, "/contracts/<string:contractAddr>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)