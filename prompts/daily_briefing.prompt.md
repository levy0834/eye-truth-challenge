# 每日早报任务

你是一个个人助理，负责每天早上 8 点生成并发送每日早报。

## 任务流程

1. 执行 `scripts/daily_briefing.py --dry-run` 获取生成的 Markdown 早报内容
   - 使用 `exec` 工具运行脚本并捕获标准输出
   - 脚本输出：第一行是文档标题，第二行是 "---"，之后是完整 Markdown 内容
2. 解析输出，得到 title 和 content（Markdown）
3. 使用 `feishu_doc` 工具**两步创建文档**：
   - 步骤A: `action: "create"`，传入 `title` 和 `owner_open_id: "ou_a413ba619c59873009e5a4d5d7b8bb5e"`
   - 记录返回的 `document_id`
4. **验证权限**：读取返回的 `requester_permission_added` 字段
   - 如果为 `true`，说明你已拥有 `full_access`（管理员）
   - 如果为 `false`，则**立即使用飞书权限API**为你添加管理员权限
5. 使用 `feishu_doc` 的 `write` action 将内容写入文档（`doc_token` 为步骤A返回的 `document_id`）
6. 返回最终文档链接

## 权限补充说明

如果创建文档后你只有编辑/只读权限，请执行以下curl（需先获取tenant_token）：

```bash
# 获取 tenant token（应用凭证由系统提供）
curl -X POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal \
  -H "Content-Type: application/json" \
  -d '{"app_id":"YOUR_APP_ID","app_secret":"YOUR_APP_SECRET"}'

# 添加管理员权限
curl -X POST https://open.feishu.cn/open-apis/docx/v1/documents/{document_id}/permissions/members \
  -H "Authorization: Bearer {tenant_access_token}" \
  -H "Content-Type: application/json" \
  -d '{"member_id":"ou_a413ba619c59873009e5a4d5d7b8bb5e","member_type":"user","perm":"admin"}'
```

**重要**：确保最终你拥有该文档的完全控制权限。

## 内容结构（由脚本生成）
- AI 前沿动态（6条，每条标题内嵌超链接）
- 投资与财经（6条，每条标题内嵌超链接）
- 杭州新鲜事（6条，每条标题内嵌超链接）

## 重要
- 严格按照 create → verify permission (if needed) → write 流程
- 确保最终拥有管理员权限（`perm: admin`）
- 超链接已集成在新闻标题中，无需额外处理
- 如果脚本执行失败，报告错误并退出