import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mydatabase"]
mycol = mydb["LOGIN"]

x = mycol.delete_many({})

print(x.deleted_count, " documents deleted.")


mycol1 = mydb["EURO-DOLLAR"]
x = mycol1.delete_many({})
print(x.deleted_count, " documents deleted.")
