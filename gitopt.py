class GitOperation:
    # 通过group查询group详情
    @staticmethod
    def get_group_detail(group):
        project_list = []
        for project in group.projects.list():
            if project.default_branch is None:
                continue
            project_detail = GitOperation.get_project_detail(project)
            project_list.append(project_detail)
        return project_list

    # 查询project详情
    @staticmethod
    def get_project_detail(project):
        description = project.description
        branch_master = project.branches.get('master')
        operate_time = branch_master.commit['committed_date']
        operator = branch_master.commit['committer_name']
        project_detail = {'id': project.id, 'name': project.name, 'description': description,
                          'operate_time': operate_time,
                          'operator': operator}
        return project_detail
