import base64
import json

import gitlab
import requests
from flask import Flask, Response, jsonify, request, session
from flask.ext.session import session
from flask_cors import CORS
import pymongo as pm

gl = gitlab.Gitlab("http://git.dev.qianmi.com",
                   private_token="wbFxyiyeM49bPUo7w8HB")
# 连接数据库
client = pm.MongoClient('localhost', 27017)
db = client.hermes
tb_user = db.user


class RestResponse(Response):
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response, (list, dict)):
            response = jsonify(response)
        return super(Response, cls).force_type(response, environ)


app = Flask(__name__)
app.response_class = RestResponse
CORS(app, resources={r"/*": {"origins": "*"}})


# ---------------------------------------------注册模块----------------------------------------------------
@app.route("/user/signUp/post", methods=['POST'])
def post_user():
    json_req = request.get_json()
    username = json_req['username']
    password = json_req['password']
    private_token = json_req['private_token']
    # 插入数据库中
    tb_user.save({'username': username, 'password': password,
                  'privateToken': private_token})
    return success_res("注册成功")

# ---------------------------------------------登陆模块----------------------------------------------------


@app.route("/user/signIn/get", methods=['GET'])
def get_user():
    json_req = request.get_json()
    username = json_req['username']
    password = json_req['password']
    cur_user = tb_user.find({'username': username})
    if cur_user is not None and cur_user['password'] is password:
        session['private_token'] = cur_user['private_token']
        return success_res("success")
    else:
        return fail_res("用户不存在或这密码错误")

# ---------------------------------------------配置模板模块------------------------------------------------------
# 数据库设计： 关于某个领域的配置吧  与一个独立的名称 name， 然后里面是一个数组：数组里面保存着字典{key:'', value:''}


@app.route("/properties/template/post")
def post_properties_template():
    pass
    # json_req = request.get_json()
    # name = json_req['name']
    # properties = json_req['properties']
    # for pro in properties:
        


@app.route("/properties/template/get")
def get_properties_template():
    pass


@app.route("/properties/template/update")
def update_properties_template():
    pass


@app.route("/properties/template/delete")
def delete_properties_template():
    pass

# ---------------------------------------------修改gitlab的模式------------------------------------------------
# 获取项目环境
# 环境的优先级 global application < product application < global application env < product application env


@app.route('/project/<project>/profile/<profile>/branch/<branch>/get')
def get_file_by_id(project, profile, branch):
    response = requests.get("http://localhost:7777/" +
                            project + "/" + profile + "/" + branch)
    properties = json.loads(response.text)
    project_public_pro = {}
    project_private_pro = {}
    project_global_pro = {}
    project_global_env_pro = {}
    for config in properties['propertySources']:
        temp = config['name'].split('/')
        if temp[-2] != project:
            # 全局共有配置
            if temp[-1] == 'application.properties' or temp[-1] == 'application.yml':
                for key, value in config['source'].items():
                    project_global_pro[key] = value
            else:
                # 该环境全局配置
                for key, value in config['source'].items():
                    project_global_env_pro[key] = value
        else:
            # 项目共有配置
            if temp[-1] == 'application.properties' or temp[-1] == 'application.yml':
                for key, value in config['source'].items():
                    project_public_pro[key] = value
            else:
                # 该环境项目私有配置
                for key, value in config['source'].items():
                    project_private_pro[key] = value
    zip_dict = {**project_global_pro, **project_global_env_pro}
    zip_dict = {**zip_dict, **project_public_pro}
    zip_dict = {**zip_dict, **project_private_pro}
    res_list = []
    v1, v2, v3, v4 = '', '', '', ''
    for key, value in zip_dict.items():
        if key in project_global_pro.keys():
            v1 = project_global_pro[key]
        if key in project_global_env_pro.keys():
            v2 = project_global_env_pro[key]
        if key in project_public_pro.keys():
            v3 = project_public_pro[key]
        if key in project_private_pro.keys():
            v4 = project_private_pro[key]
        res_list.append({'key': key, 'global': v1,
                         'global_env': v2, 'project': v3, 'project_env': v4})
    return success_res({
        "res_list": res_list
    })


# 修改项目中的公共配置
@app.route("/project/<project>/get", methods=["POST"])
def post_project_config(project):
    json_req = request.get_json()
    put_configurations(json_req, project + "/application.properties")
    return success_res("success")


# 修改项目中环境的配置
@app.route("/project/<project>/profile/<profile>/put", methods=["POST"])
def post_project_env_config(project, profile):
    json_req = request.get_json()
    put_configurations(json_req, project +
                       "/application-" + profile + ".properties")
    return success_res("success")


# 修改全局的配置
@app.route("/global/put", methods=["POST"])
def post_global_config():
    json_req = request.get_json()
    put_configurations(json_req, "application.properties")
    return success_res("success")


# 修改全局中环境的配置
@app.route("/global/profile/<profile>/put", methods=['POST'])
def post_global_env_config(profile):
    json_req = request.get_json()
    put_configurations(json_req, "application-" + profile + ".properties")
    return success_res("success")


# 新增全局中的配置
@app.route("/global/post", methods=["POST"])
def add_global_config():
    json_req = request.get_json()
    post_configurations(json_req, "application.properties")
    return success_res("success")


# 新增全局环境中的配置
@app.route("/global/profile/<profile>/post", methods=["POST"])
def add_global_env_config(profile):
    json_req = request.get_json()
    post_configurations(json_req, "application-" + profile + ".properties")
    return success_res("success")


# 新增项目环境中的配置
@app.route("/project/<project>/profile/<profile>/post", methods=["POST"])
def add_project_env_config(project, profile):
    json_req = request.get_json()
    post_configurations(json_req, project +
                        "/application" + profile + ".properties")
    return success_res("success")


# 新增项目中的配置
@app.route("/project/<project>/post", methods=["POST"])
def add_project_config(project):
    json_req = request.get_json()
    post_configurations(json_req, project + "/application.properties")
    return success_res("success")


# 展示所有的项目
@app.route("/projects/get", methods=["GET"])
def get_projects():
    repo = gl.projects.get('bm-life/spring-cloud-config-center')
    projects = repo.repository_tree()
    project_list = [pro['name'] for pro in projects if pro['type'] == 'tree']
    return success_res(project_list)


# 成功返回的结果
def success_res(data, code=200):
    return {
        'code': code,
        'data': data,
        'message': 'success'
    }


# 失败返回的结果
def fail_res(code=400, message='fail'):
    return {
        'code': code,
        'message': message
    }


# 获取远程的文件
def get_git_files(file_path):
    project = gl.projects.get('bm-life/spring-cloud-config-center')
    temp = project.files.get(file_path=file_path, ref="master")
    file = base64.b64decode(temp.content)
    str_config = file.decode('utf-8')
    return temp, str_config.splitlines()


# update配置
def put_configurations(json_req, file_path):
    file, config_list = get_git_files(file_path)
    temp_list = []
    for k, v in json_req.items():
        for config in config_list:
            temp = config.split("=")
            if temp[0] == k:
                temp_list.append(k + "=" + v)
            else:
                temp_list.append(config)
    str_config = "\n".join(temp_list)
    file.content = base64.b64encode(str.encode(str_config)).decode()
    file.save(branch_name='master', commit_message=str(json_req.keys()))


# 新增配置
def post_configurations(json_req, file_path):
    file, config_list = get_git_files(file_path)
    for k, v in json_req:
        config_list.append(k + "=" + v)
    res = "\n".join(config_list)
    file.content = base64.b64encode(str.encode(res)).decode()
    file.save(branch_name='master', commit_message=str(json_req.keys()))


if __name__ == '__main__':
    app.run(debug=False, port=8080, host='0.0.0.0')
