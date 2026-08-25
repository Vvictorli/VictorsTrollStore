# Victor's TrollStore Source

一个自动追踪上游 GitHub Release 中 `.ipa` 文件的 TrollStore 应用源。目前收录：

- [PiliPlus](https://github.com/bggRGjQaUbCoE/PiliPlus)
- [TiebaPure-iOS16](https://github.com/2218164692/TiebaPure-iOS16)
- [PureLive](https://github.com/liuchuancong/pure_live)
- [Aidoku](https://github.com/Aidoku/Aidoku)

## 使用

仓库推送到 GitHub 后，将下面地址添加到 TrollStore 或兼容此 JSON 格式的客户端：

```text
https://raw.githubusercontent.com/Vvictorli/VictorsTrollStore/main/apps.json
```

如果你的仓库名或默认分支不同，请替换地址中的仓库名或 `main`。同时修改
`config/source.json` 中的 `sourceURL` 和 `website`；GitHub Actions 运行时会自动按实际仓库与分支修正生成文件中的 `sourceURL`。

## 自动更新

`.github/workflows/update-source.yml` 每天北京时间 08:20 检查一次，也支持在 GitHub 仓库的
**Actions → Update TrollStore source → Run workflow** 手动刷新。检测到新 IPA 后才会提交 `apps.json`。

首次推送后，请在仓库的 **Settings → Actions → General → Workflow permissions** 中确认已允许
**Read and write permissions**。工作流使用 GitHub 自动提供的 `GITHUB_TOKEN`，不需要自己配置密钥。

## 本地刷新与新增应用

```bash
python3 scripts/update_source.py
python3 -m unittest discover -s tests -v
```

新增应用时，在 `config/apps.json` 加入项目配置，尤其要让 `assetPattern` 只匹配 iOS IPA。
生成脚本会忽略草稿版和预发行版，并从最近 20 个正式 Release 中寻找最新匹配资源。
