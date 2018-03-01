import pymongo as pm

client = pm.MongoClient('localhost', 32768)
db = client.test
tb_user = db.user

tb_user.save({"username": 'zmy', 'password': '123',
              'private_token': 'jfdkajflkdsa'})


res = tb_user.find({"username": "zmy"})

for i in res:
    print(i)
# print(res["_id"])



