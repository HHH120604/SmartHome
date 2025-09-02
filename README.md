# SmartHome
## git使用
- 克隆该项目：`git clone https://github.com/HHH120604/SmartHome.git`
- 查看分支：`git branch -a`
- 创建并切换分支：`git checkout -b <分支名称>`
  > 分支名称使用`python/hhh1206`架构+自己的代称, 便于提交定位
  > 注: 之后使用`<>`表示必须参数的注释, 使用时需去掉括号. 使用`[]`表示可选参数注释, 同样需去掉括号
- 修改完成后提交更改
  - 如有新增文件: `git add <文件路径>`
    > 可使用`git add .`快速添加所有新增文件，注意可能会添加进不需要的文件
  - 提交：`git commit -m "<提交说明>"`
    > 注意双引号，否则中文或其它字符可能出错
  - 推送到远程服务器：`git push origin <本地分支:远程分支>`
    > push是操作；origin是远程仓库地址的代称
- 创建关联：`git branch --set-upstream-to=origin/<远程分支> <本地分支>`
  > 创建关联后使用pull操作无需再次指定名称
- 拉取最新代码：`git pull <远程分支名称>`
  > 需要拉取的分支名称(ohos、python、uniapp)，每次写代码前都拉取一次是个好习惯:star:
E:.
├─.vscode
├─ohos
├─python
│  ├─app
│  │  ├─api
│  │  ├─models
│  │  ├─schemas
│  │  ├─services
│  │  └─utils
│  └─test
└─uniapp