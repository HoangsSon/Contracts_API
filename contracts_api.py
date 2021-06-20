from flask import Flask
from flask_restful import Api, Resource, abort
from flask_pymongo import PyMongo
import json
from bson import ObjectId
import os
import requests

app = Flask(__name__)
api = Api(app)
app.config["MONGO_URI"] = "mongodb://localhost:27017/contracts"
mongo = PyMongo(app)


API_KEY = "" # Your Etherscan API. If you don't have API Key. Try to visit this page: https://etherscan.io/apis


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


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
        contractAnalysis = mongo.db.analysis.find(myquery, {"_id":0})
        if contractAnalysis.count() == 0: # no document found in database
            sourcecode = tryGetSourceEtherscan(contractAddr) # try to find sourcecode on Etherscan
            if len(sourcecode) > 0: # use regex to check sourcecode
                f = open("./contracts/"+contractAddr+".sol", "w")
                f.write(sourcecode)
                f.close()
                os.system("python ./honeybadger/honeybadger.py -j -s ./contracts/"+contractAddr+".sol")
                f = open("./results/"+contractAddr+".json", "r")
                j = f.read()
                f.close()
                j = j[1:-1].split("},{")
                for i in range(len(j)):
	                j[i] = "{"+j[i]+"}"
                for i in range(len(j)):
                    mongo.db.analysis.insert(json.loads(j[i]))
                if len(j) > 1:
                    for i in range(len(j)):
                        a = json.loads(j[i])
                        if a["balance_disorder"] != False or a["hidden_state_update"] != False or a["hidden_transfer"] != False or a["straw_man_contract"] != False or a["skip_empty_string_literal"] != False or a["inheritance_disorder"] != False or a["uninitialised_struct"] != False:
                            return a
                    return json.loads(j[len(j) - 1])
                else:
                    return json.loads(j[0])
            else:
                return abort(404, description="Contract Address not found...")
        elif contractAnalysis.count() == 1:
            return contractAnalysis[0]
        else:
            for x in contractAnalysis:
                if x["balance_disorder"] != False or x["hidden_state_update"] != False or x["hidden_transfer"] != False or x["straw_man_contract"] != False or x["skip_empty_string_literal"] != False or x["inheritance_disorder"] != False or x["uninitialised_struct"] != False:
                    return x
            return mongo.db.analysis.find_one(myquery, {"_id":0})

api.add_resource(contracts, "/contracts/<string:contractAddr>")

if __name__ == "__main__":
    app.run()
