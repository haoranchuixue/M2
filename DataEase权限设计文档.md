# DataEase 社区版权限管理设计文档

> 版本：v1.0  
> 日期：2026-03-28  
> 基于 DataEase v2.10.20-custom

---

## 一、整体架构

### 1.1 权限模型概览

采用 **RBAC（基于角色的访问控制）** 模型，参考 Metabase 权限设计，分为四层：

```
┌─────────────────────────────────────────────────┐
│                  用户 (User)                      │
│                    ↓ 多对多                        │
│                  角色 (Role)                       │
│           ↙      ↓       ↓       ↘              │
│     菜单权限  资源权限  行权限  列权限              │
│     (Menu)  (Resource) (Row)  (Column)            │
└─────────────────────────────────────────────────┘
```

| 层级 | 控制粒度 | 存储表 | 说明 |
|------|---------|--------|------|
| 菜单权限 | 页面/功能入口 | `de_role_menu` | 控制角色可见的菜单项 |
| 资源权限 | 数据源/数据集/仪表板/数据大屏 | `de_role_resource` | 控制角色对资源的访问级别 |
| 行权限 | 数据集行级过滤 | `de_role_row_permission` | 按角色过滤数据集查询结果的行 |
| 列权限 | 数据集列级可见性 | `de_role_column_permission` | 按角色隐藏数据集的特定字段 |

### 1.2 系统菜单入口

权限管理作为独立菜单位于 **系统设置** 侧边栏，与「用户管理」「角色管理」并列。

```
系统设置
 ├── 用户管理
 ├── 角色管理      ← 仅保留成员管理
 ├── 权限管理      ← 统一权限配置入口
 │    ├── 数据      (数据源/数据集 资源权限)
 │    ├── 集合      (仪表板/数据大屏 资源权限)
 │    ├── 菜单      (角色菜单权限)
 │    └── 行列权限   (数据集行列级权限)
 ├── 系统参数
 └── 字体管理
```

---

## 二、数据库设计

### 2.1 角色表 `de_role`

```sql
CREATE TABLE de_role (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(128)    NOT NULL,
  `desc`      VARCHAR(512),
  readonly    TINYINT(1)      NOT NULL DEFAULT 0,  -- 系统内置角色标记
  root        TINYINT(1)      NOT NULL DEFAULT 0,  -- 超级管理员标记
  create_time BIGINT
);
```

- `readonly=1` 的角色为系统内置角色（如"系统管理员"），不可删除/修改权限
- `root=1` 的角色拥有所有权限，跳过权限检查

### 2.2 菜单权限表 `de_role_menu`

```sql
CREATE TABLE de_role_menu (
  id      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  role_id BIGINT UNSIGNED NOT NULL,
  menu_id BIGINT UNSIGNED NOT NULL,
  UNIQUE KEY uk_role_menu (role_id, menu_id)
);
```

- 存储角色与菜单的关联关系
- 未关联的菜单对该角色不可见
- `root` 角色跳过菜单过滤，默认显示所有菜单

### 2.3 资源权限表 `de_role_resource`

```sql
CREATE TABLE de_role_resource (
  id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  role_id          BIGINT UNSIGNED NOT NULL,
  resource_id      VARCHAR(50)     NOT NULL,
  resource_type    VARCHAR(20)     NOT NULL,   -- datasource|dataset|dashboard|dataV
  permission_level VARCHAR(20)     NOT NULL DEFAULT 'view',
  UNIQUE KEY uk_role_resource (role_id, resource_id, resource_type)
);
```

**权限级别 `permission_level`：**

| 值 | 含义 | 说明 |
|----|------|------|
| `manage` | 无限制 | 完全访问，可查看、编辑、删除 |
| `view` | 可查看 | 只读访问 |
| `none` | 禁止访问 | 不可见（默认，无记录时等效） |

**资源类型 `resource_type`：**

| 值 | 对应资源 |
|----|---------|
| `datasource` | 数据源 |
| `dataset` | 数据集 |
| `dashboard` | 仪表板 |
| `dataV` | 数据大屏 |

### 2.4 行权限表 `de_role_row_permission`

```sql
CREATE TABLE de_role_row_permission (
  id                BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  role_id           BIGINT UNSIGNED NOT NULL,
  dataset_id        VARCHAR(50)     NOT NULL,
  filter_expression TEXT,             -- SQL WHERE 条件片段
  enable            TINYINT(1)      NOT NULL DEFAULT 1,
  UNIQUE KEY uk_role_dataset (role_id, dataset_id)
);
```

- `filter_expression` 为 SQL WHERE 子句片段，例如 `region = 'East' AND status = 1`
- `enable` 控制是否启用该规则
- 查询数据集时，将匹配角色的过滤表达式追加到 WHERE 条件

### 2.5 列权限表 `de_role_column_permission`

```sql
CREATE TABLE de_role_column_permission (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  role_id     BIGINT UNSIGNED NOT NULL,
  dataset_id  VARCHAR(50)     NOT NULL,
  column_name VARCHAR(200)    NOT NULL,
  visible     TINYINT(1)      NOT NULL DEFAULT 1,
  UNIQUE KEY uk_role_dataset_col (role_id, dataset_id, column_name)
);
```

- `visible=0` 表示该角色不可见该列
- 未配置的列默认可见 (`visible=1`)
- 返回数据集结果时，过滤掉不可见的列

### 2.6 ER 关系图

```
de_role  ──1:N──  de_role_menu             ──N:1──  core_menu
    │
    ├───1:N──  de_role_resource
    │
    ├───1:N──  de_role_row_permission      ──N:1──  core_dataset_group
    │
    └───1:N──  de_role_column_permission   ──N:1──  core_dataset_table_field
```

---

## 三、后端 API 设计

所有权限 API 统一在 `CommunityPermissionServer` 控制器中，路径前缀 `/permission`。

### 3.1 通用 API

| 方法 | 路径 | 说明 | 返回 |
|------|------|------|------|
| GET | `/permission/roles` | 获取所有角色列表 | `List<RoleVO>` |

### 3.2 资源权限 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/permission/resources/{type}` | 获取指定类型的资源列表 |
| GET | `/permission/byResource?resourceType=&resourceId=` | 以资源为中心，查看所有角色对该资源的权限 |
| GET | `/permission/byRole/{roleId}?resourceType=` | 以角色为中心，查看该角色对所有资源的权限 |
| POST | `/permission/saveByResource` | 保存某资源的所有角色权限 |
| POST | `/permission/saveByRole` | 保存某角色的所有资源权限 |

**请求体示例 — `saveByResource`：**
```json
{
  "resourceId": "985189053949415424",
  "resourceType": "dataset",
  "permissions": [
    { "roleId": 1, "permLevel": "manage" },
    { "roleId": 2, "permLevel": "view" }
  ]
}
```

### 3.3 菜单权限 API（复用已有接口）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/menu/allList` | 获取全量菜单树（含 i18n 翻译） |
| GET | `/role/menu/list/{roleId}` | 获取角色已勾选的菜单 ID 列表 |
| POST | `/role/menu/save` | 保存角色的菜单权限 |

### 3.4 行列权限 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/permission/datasets` | 获取所有数据集列表（非文件夹） |
| GET | `/permission/datasetFields/{datasetId}` | 获取数据集的字段列表 |
| GET | `/permission/rowPerms/{datasetId}` | 获取数据集的所有角色行权限配置 |
| POST | `/permission/rowPerms/save` | 保存数据集的行权限 |
| GET | `/permission/colPerms/{roleId}/{datasetId}` | 获取角色对数据集的列可见性 |
| POST | `/permission/colPerms/save` | 保存列可见性 |

**请求体示例 — `rowPerms/save`：**
```json
{
  "datasetId": "985189053949415424",
  "permissions": [
    { "roleId": 1, "filterExpression": "", "enable": false },
    { "roleId": 2, "filterExpression": "region = 'East'", "enable": true }
  ]
}
```

**请求体示例 — `colPerms/save`：**
```json
{
  "roleId": 2,
  "datasetId": "985189053949415424",
  "columns": [
    { "columnName": "salary", "visible": false },
    { "columnName": "name", "visible": true }
  ]
}
```

---

## 四、前端页面设计

### 4.1 权限管理页面 `/sys-setting/permission`

路由注册在 `core_menu` 表中，组件为 `system/permission/index.vue`。

**Tab 结构：**

| Tab | 左面板 | 右面板 |
|-----|--------|--------|
| **数据** | 角色/资源切换 + 数据源/数据集选择 | 权限矩阵（下拉选择 无限制/可查看/禁止访问） |
| **集合** | 角色/资源切换 + 仪表板/数据大屏选择 | 同上 |
| **菜单** | 角色列表 | 菜单树 + 复选框勾选 |
| **行列权限** | 数据集列表 | 行权限表格 + 列权限配置 |

### 4.2 角色管理页面 `/sys-setting/role`

仅保留 **成员管理** 功能，直接展示角色成员列表，无 Tab 切换。菜单权限已移至权限管理页面。

---

## 五、Java 代码结构

```
io.dataease.community
 ├── entity/
 │    ├── DeRole.java                   # 角色实体
 │    ├── DeRoleMenu.java               # 角色-菜单关联
 │    ├── DeRoleResource.java           # 角色-资源权限
 │    ├── DeRoleRowPermission.java      # 行权限
 │    ├── DeRoleColumnPermission.java   # 列权限
 │    └── DeUserRole.java               # 用户-角色关联
 ├── mapper/
 │    ├── DeRoleMapper.java
 │    ├── DeRoleMenuMapper.java
 │    ├── DeRoleResourceMapper.java
 │    ├── DeRoleRowPermissionMapper.java
 │    └── DeRoleColumnPermissionMapper.java
 ├── dto/
 │    ├── PermissionSaveDTO.java        # 按资源保存权限
 │    ├── PermissionSaveByRoleDTO.java  # 按角色保存权限
 │    ├── RolePermissionVO.java         # 角色权限视图
 │    ├── ResourcePermissionVO.java     # 资源权限视图
 │    ├── ResourceItemVO.java           # 资源列表项
 │    ├── RowPermVO.java                # 行权限视图
 │    ├── RowPermSaveDTO.java           # 行权限保存
 │    ├── ColPermVO.java                # 列权限视图
 │    ├── ColPermSaveDTO.java           # 列权限保存
 │    ├── DatasetFieldVO.java           # 数据集字段
 │    └── MenuTreeNodeVO.java           # 菜单树节点
 └── server/
      └── CommunityPermissionServer.java  # 统一权限 REST 控制器
```

---

## 六、权限执行流程

### 6.1 菜单权限执行

```
用户登录
  → MenuServer.query() 获取菜单列表
    → 查询用户关联的角色 (de_user_role)
    → 若任一角色为 root → 返回全部菜单
    → 否则合并所有角色的 de_role_menu → 过滤菜单树
  → 前端根据返回的菜单列表动态生成路由
```

### 6.2 资源权限执行

```
用户访问资源列表（数据源/数据集/仪表板/数据大屏）
  → RoleResourcePermissionManage 拦截查询
    → 查询用户角色
    → 查询 de_role_resource 获取有权限的 resource_id 集合
    → 过滤资源列表，仅返回有权限的资源
```

### 6.3 行列权限执行（配置阶段已完成，执行侧待深度集成）

```
数据集查询执行
  → 检查用户角色的 de_role_row_permission
    → 若 enable=1 且 filter_expression 非空
    → 追加 WHERE 条件到查询 SQL
  → 检查 de_role_column_permission
    → 过滤 visible=0 的列，不返回给前端
```

---

## 七、安全考量

1. **默认拒绝**：未配置权限的资源默认为「禁止访问」(`none`)
2. **系统角色保护**：`readonly=1` 的角色不允许修改权限配置
3. **超级管理员**：`root=1` 的角色跳过所有权限检查
4. **SQL 注入防护**：行权限的 `filter_expression` 为管理员配置，应确保仅由受信任的管理员操作
5. **前后端双重校验**：菜单权限在前端路由和后端 API 两层执行

---

## 八、后续演进方向

| 方向 | 说明 |
|------|------|
| 行权限执行集成 | 在数据集查询引擎中深度集成 `filter_expression` 的 SQL 注入 |
| 列权限执行集成 | 在数据集字段返回和图表渲染时过滤不可见列 |
| 数据脱敏 | 在列权限基础上增加脱敏规则（如手机号中间四位替换为 `****`） |
| 审计日志 | 记录权限变更操作日志 |
| 权限继承 | 支持文件夹级别的权限继承（子资源自动继承父文件夹权限） |
| 用户组 | 引入用户组概念，简化大规模用户的权限分配 |
